"""
Router de Administração.
POST /api/admin/register_client → cadastra vínculo Contato → Cliente.
POST /api/admin/upload_month → faz upload de um CSV para novo mês.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

from backend.core.auth import require_admin
from backend.core.config import get_settings
from backend.models.schemas import RegisterClientRequest, RegisterClientResponse, UploadMonthResponse

from backend.services.mapping_service import cadastrar_novo_cliente
from backend.services.bigquery_service import get_bq_client

# Helper for normalized BQ uploads
import io
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["Administração"])


@router.post("/register_client", response_model=RegisterClientResponse)
async def register_client(
    request: RegisterClientRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Cadastra um novo vínculo Contato → Cliente no statusContatos.xlsx.
    Restrito a administradores.
    """
    print(f"[DEBUG] Rota register_client chamada: {request.nome_contato} -> {request.nome_cliente}")
    sucesso, msg = cadastrar_novo_cliente(
        request.nome_contato.strip().upper(),
        request.nome_cliente.strip().upper(),
    )

    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    return RegisterClientResponse(success=True, message=msg)


@router.post("/upload_month", response_model=UploadMonthResponse)
async def upload_month(
    nome: str = Form(..., description="Nome do arquivo (ex: 2026_03)"),
    arquivo: UploadFile = File(..., description="Arquivo CSV do mês"),
    current_user: dict = Depends(require_admin),
):
    """
    Upload de um arquivo CSV para criar um novo mês local.
    Restrito a administradores.
    """
    settings = get_settings()

    # Validação do nome
    filename = nome.strip()
    if not filename.endswith(".csv"):
        filename += ".csv"

    # Garante que a pasta existe
    if not os.path.exists(settings.DATA_DIR):
        os.makedirs(settings.DATA_DIR)

    # Salva diretamente no BigQuery (Sem salvar no disco)
    try:
        content = await arquivo.read()
        
        # Parse CSV (Detect separator)
        # Try semicolon first (common in Brazil)
        try:
            df = pd.read_csv(io.BytesIO(content), sep=";", encoding="utf-8")
        except:
             try:
                 df = pd.read_csv(io.BytesIO(content), sep=";", encoding="latin1")
             except:
                 # Fallback to comma
                 df = pd.read_csv(io.BytesIO(content), sep=",")

        # Normalize Columns for BQ (replace spaces with underscores)
        df.rename(columns={
            "Atendido por": "Atendido_por",
            "Nome Cliente": "Nome_Cliente",
            "Data Início": "Data_Inicio"
        }, inplace=True)
        
        # FIX DATE PARSING (Day/Month Swap)
        # The user reported that "02/05" was being read as "May 2nd" instead of "Feb 5th".
        # We must enforce dayfirst=True for DD/MM/YYYY format commonly used in Brazil.
        if "Data" in df.columns:
            # --- TRATAMENTO ROBUSTO DE DATAS (Igual data_service.py) ---
            # O upload anterior quebrava ISO dates (YYYY-MM-DD) ao forçar dayfirst=True.
            
            # Garantir string e tratar Nulos
            if not pd.api.types.is_string_dtype(df["Data"]):
                df["Data"] = df["Data"].astype(str)
                df["Data"].replace(["None", "nan", "<NA>"], pd.NA, inplace=True)

            # 1. Tenta padrão BR (dia primeiro)
            df["Data_Parsed"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
            
            # Identifica falhas reais
            mask_falha = df["Data_Parsed"].isna() & df["Data"].notna() & (df["Data"] != "NaT") & (df["Data"] != "")

            # 2. Tenta padrão US/ISO (mês primeiro ou YYYY-MM-DD) para os que falharam
            if mask_falha.any():
                print(f"DEBUG UPLOAD: {mask_falha.sum()} datas falharam com dayfirst=True. Tentando dayfirst=False.")
                df.loc[mask_falha, "Data_Parsed"] = pd.to_datetime(df.loc[mask_falha, "Data"], dayfirst=False, errors="coerce")

            df["Data"] = df["Data_Parsed"]
            df.drop(columns=["Data_Parsed"], inplace=True)
            # -----------------------------------------------------------
            
            # EXTRACT TIME TO HORA BEFORE TRUNCATING DATA
            # If Hora is missing or empty/zero, try to get it from Data timestamp
            if "Hora" not in df.columns:
                df["Hora"] = df["Data"].dt.strftime("%H:%M")
            else:
                df["Hora"] = df["Hora"].astype(str)
                # Replace invalid or empty times with extracted time
                invalid_times = ["nan", "None", "", "00:00", "00:00:00", "0:00"]
                mask = df["Hora"].isin(invalid_times) | df["Hora"].isna()
                if mask.any():
                     df.loc[mask, "Hora"] = df.loc[mask, "Data"].dt.strftime("%H:%M")

            # Format back to ISO string (YYYY-MM-DD) for BigQuery DATE/STRING compatibility
            df["Data"] = df["Data"].dt.strftime("%Y-%m-%d")
            
        if "Hora" in df.columns:
            df["Hora"] = df["Hora"].astype(str)

        project_id = settings.BQ_PROJECT
        dataset_id = settings.BQ_DATASET
        table_id = f"{project_id}.{dataset_id}.atendimentos_{filename.replace('.csv', '')}"

        client = get_bq_client()
        if not client:
             raise HTTPException(status_code=500, detail="BigQuery Error")
             
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE", # Replace if exists
            autodetect=True, # Allow schema inference
            source_format=bigquery.SourceFormat.PARQUET 
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()

        return UploadMonthResponse(
            success=True,
            message=f"Mês {filename} carregado para BigQuery com sucesso!",
            filename=filename,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}",
        )


@router.post("/upload_base")
async def upload_base(
    file: UploadFile = File(..., description="Arquivo statusContatos.xlsx"),
    current_user: dict = Depends(require_admin),
):
    """
    Substitui o arquivo statusContatos.xlsx (base De/Para global).
    Restrito a administradores.
    """
    settings = get_settings()
    map_path = settings.MAPPING_FILE

    try:
        content = await file.read()
        
        # Parse Excel
        df_map = pd.read_excel(io.BytesIO(content), engine="openpyxl")
        
        # Normalize Columns
        # Look for "NOME DO CONTATO" and "NOME CLIENTE"
        cols_map = {c.upper(): c for c in df_map.columns}
        
        if "NOME DO CONTATO" not in cols_map or "NOME CLIENTE" not in cols_map:
             raise HTTPException(status_code=400, detail="Colunas 'NOME DO CONTATO' e 'NOME CLIENTE' necessárias.")
             
        df_clean = df_map[[cols_map["NOME DO CONTATO"], cols_map["NOME CLIENTE"]]].copy()
        df_clean.columns = ["original_name", "normalized_name"]
        
        # Clean
        df_clean["original_name"] = df_clean["original_name"].astype(str).str.strip().str.upper()
        df_clean["normalized_name"] = df_clean["normalized_name"].astype(str).str.strip()
        df_clean = df_clean.drop_duplicates(subset=["original_name"])
        df_clean = df_clean[df_clean["original_name"] != "NAN"]
        df_clean = df_clean[df_clean["original_name"] != ""]
        
        df_clean["updated_at"] = datetime.utcnow().isoformat()
        
        # Load to BQ
        client = get_bq_client()
        if not client:
             raise HTTPException(status_code=500, detail="BigQuery Error")
             
        table_id = f"{settings.BQ_PROJECT}.{settings.BQ_DATASET}.config_client_mapping"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            schema=[
                bigquery.SchemaField("original_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("normalized_name", "STRING", mode="REQUIRED"),
                bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE"),
            ]
        )
        
        job = client.load_table_from_dataframe(df_clean, table_id, job_config=job_config)
        job.result()

        return {"success": True, "message": "Base atualizada no BigQuery com sucesso!"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar base: {str(e)}",
        )

