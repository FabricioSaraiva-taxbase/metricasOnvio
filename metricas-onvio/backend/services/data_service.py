"""
Serviço principal de dados: listar meses e carregar dados de atendimento.
Portado de app_metricas.py (linhas 749-888), removendo dependência do Streamlit.
"""

import glob
import os
from typing import Dict, List, Optional

import pandas as pd

from backend.core.config import get_settings
from backend.services.bigquery_service import HAS_BQ, get_bq_client
from backend.services.mapping_service import aplicar_depara


def listar_arquivos_por_ano() -> Dict[str, List[dict]]:
    """
    Lista meses disponíveis agrupados por ano.
    Híbrido: BigQuery (nuvem) + CSVs locais, sem duplicatas.

    Retorna:
        dict[ano, list[{caminho, display, mes_raw}]]
    """
    settings = get_settings()
    estrutura: Dict[str, List[dict]] = {}
    meses_na_nuvem: set = set()

    # Garante que a pasta data/ existe
    if not os.path.exists(settings.DATA_DIR):
        os.makedirs(settings.DATA_DIR)

    # 1. LISTAR DO BIGQUERY (NUVEM)
    if HAS_BQ:
        try:
            client = get_bq_client()
            if client:
                print(f"DEBUG: Listing tables for {settings.BQ_DATASET} in {client.project}")
                dataset_ref = client.dataset(settings.BQ_DATASET)
                tables = list(client.list_tables(dataset_ref))
                print(f"DEBUG: Found {len(tables)} tables.")

                for table in tables:
                    tid = table.table_id
                    print(f"DEBUG: Checking table {tid}")
                    if tid.startswith("atendimentos_"):
                        partes = tid.split("_")  # [atendimentos, 2026, 01]
                        if len(partes) >= 3:
                            ano, mes = partes[1], partes[2]
                            if ano not in estrutura:
                                estrutura[ano] = []

                            meses_na_nuvem.add(f"{ano}_{mes}")

                            estrutura[ano].append(
                                {
                                    "caminho": f"BQ:{ano}_{mes}",
                                    "display": f"{mes}/{ano[2:]} ☁️",
                                    "mes_raw": int(mes) if mes.isdigit() else 0,
                                }
                            )
        except Exception as e:
            print(f"DEBUG BQ EXCEPTION (listar_arquivos_por_ano): {e}")
            pass

    # 2. LISTAR DO DISCO (LOCAL) - COM FILTRO DE DUPLICIDADE
    arquivos = glob.glob(os.path.join(settings.DATA_DIR, "*.csv"))
    for f in arquivos:
        nome_base = os.path.basename(f).replace(".csv", "")
        partes = nome_base.split("_", 1)  # Ex: 2026_01

        if len(partes) == 2:
            ano = partes[0]
            resto = partes[1]
            mes_limpo = resto.split(" ")[0]

            # Se já tem na nuvem, ignora o local
            if f"{ano}_{mes_limpo}" in meses_na_nuvem:
                continue

            if ano.isdigit() and len(ano) == 4:
                if ano not in estrutura:
                    estrutura[ano] = []

                mes_num_str = resto[:2]
                try:
                    mes_int = int(mes_num_str)
                except ValueError:
                    mes_int = 0

                sufixo = resto[2:]
                display = f"{mes_num_str}/{ano[2:]}{sufixo}"

                estrutura[ano].append(
                    {"caminho": f, "display": display, "mes_raw": mes_int}
                )

    # Ordenação: meses decrescentes dentro de cada ano, anos decrescentes
    for ano in estrutura:
        estrutura[ano] = sorted(
            estrutura[ano], key=lambda x: x["mes_raw"], reverse=True
        )

    return dict(sorted(estrutura.items(), reverse=True))


def carregar_dados_mes(identificador: str) -> Optional[pd.DataFrame]:
    """
    Carrega dados de atendimento de um mês específico.
    Suporta BigQuery (prefixo 'BQ:') ou arquivo CSV local.
    Aplica normalização, cruzamento De/Para e tratamento de datas.

    Args:
        identificador: 'BQ:2026_01' ou caminho de um CSV.

    Returns:
        DataFrame processado ou None se falhar.
    """
    settings = get_settings()
    df = None

    # --- TENTATIVA 1: BIGQUERY (NUVEM) ---
    if isinstance(identificador, str) and identificador.startswith("BQ:") and HAS_BQ:
        try:
            partes = identificador.replace("BQ:", "").split("_")
            if len(partes) >= 2:
                ano, mes = partes[0], partes[1]
                tabela = f"atendimentos_{ano}_{mes}"
                client = get_bq_client()
                if client:
                    query = f"SELECT * FROM `{settings.BQ_PROJECT}.{settings.BQ_DATASET}.{tabela}`"
                    df = client.query(query).to_dataframe()
                    
                    # Remap columns from BQ (No Spaces) to Frontend (Spaces)
                    df.rename(columns={
                        "Atendido_por": "Atendido por",
                        "Nome_Cliente": "Nome Cliente",  # If exists
                        "Data_Inicio": "Data Início"     # If exists
                    }, inplace=True)
        except Exception as e:
            print(f"DEBUG BQ EXCEPTION (carregar_dados_mes): {e}")
            pass

    # --- TENTATIVA 2: CSV LOCAL ---
    if df is None:
        # Se é um caminho relativo, resolve contra DATA_DIR
        csv_path = identificador
        if not os.path.isabs(csv_path) and not csv_path.startswith("BQ:"):
            csv_path = os.path.join(settings.DATA_DIR, csv_path)

        if not os.path.exists(csv_path):
            return None

        try:
            try:
                df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
            except Exception:
                df = pd.read_csv(csv_path, sep=";", encoding="latin1")
        except Exception:
            return None

    if df is None:
        return None

    # --- CRUZAMENTO DE/PARA ---
    df = aplicar_depara(df)

    # --- TRATAMENTO DE DATAS ---
    if "Data" in df.columns:
        # Garante que None/NaN seja tratado como string fazia, mas preservando nulos
        if not pd.api.types.is_string_dtype(df["Data"]):
             df["Data"] = df["Data"].astype(str)
             df["Data"].replace(["None", "nan", "<NA>"], pd.NA, inplace=True)

        # 1. Tenta padrão BR (dia primeiro)
        # 2. Se falhar, tenta padrão US (mês primeiro) para os que deram erro (NaT)
        
        # Conversão Inicial (BR - Dia Primeiro)
        df["Data_Parsed"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
        
        # Identifica falhas reais (onde TINHA dado mas falhou o parser)
        # Ignora onde já era Nulo na origem
        mask_falha = df["Data_Parsed"].isna() & df["Data"].notna() & (df["Data"] != "NaT") & (df["Data"] != "nan") & (df["Data"] != "")

        # Tentativa 2: Padrão US (Mês Primeiro) APENAS para os que falharam
        if mask_falha.any():
            print(f"WARN: {mask_falha.sum()} datas falharam com dayfirst=True. Tentando dayfirst=False.")
            df.loc[mask_falha, "Data_Parsed"] = pd.to_datetime(df.loc[mask_falha, "Data"], dayfirst=False, errors="coerce")

        # Tentativa 3: Inferência automática (último recurso)
        mask_falha_2 = df["Data"].notna() & (df["Data"] != "") & df["Data_Parsed"].isna() & ~mask_falha
        # Nota: mask_falha já foi tratada, então verificamos se AINDA tem falha
        # Mas simplificando: quem ainda é NaT e tinha valor original
        mask_persistente = df["Data_Parsed"].isna() & df["Data"].notna() & (df["Data"] != "NaT") & (df["Data"] != "nan") & (df["Data"] != "")
        
        if mask_persistente.any():
            print(f"WARN: {mask_persistente.sum()} datas ainda falhando. Tentando inferência total.")
            df.loc[mask_persistente, "Data_Parsed"] = pd.to_datetime(df.loc[mask_persistente, "Data"], errors="coerce")

        df["Data"] = df["Data_Parsed"]
        df.drop(columns=["Data_Parsed"], inplace=True)

        if df["Data"].dt.tz is not None:
             df["Data"] = df["Data"].dt.tz_localize(None)
        
        df["Dia"] = df["Data"].dt.date
        df = df.sort_values(by="Data", ascending=False)

    return df


def carregar_periodo_meses(lista_meses: List[str]) -> Optional[pd.DataFrame]:
    """
    Carrega dados de múltiplos meses de uma vez.
    Otimizado para BigQuery usando Wildcard Tables (_TABLE_SUFFIX).
    
    Args:
        lista_meses: Lista de identificadores ex: ['2026_01', '2026_02'] (sem prefixo BQ: ou extensão)
        
    Returns:
        DataFrame concatenado ou None.
    """
    if not lista_meses:
        return None
        
    settings = get_settings()
    df_final = None

    # Tenta Otimização BigQuery se todos forem formato YYYY_MM
    if HAS_BQ:
        # Verifica se todos parecem ser YYYY_MM
        valid_formats = all(len(m) == 7 and "_" in m for m in lista_meses)
        
        if valid_formats:
            try:
                # Ordena para pegar min e max para o BETWEEN
                sorted_meses = sorted(lista_meses)
                start = sorted_meses[0]
                end = sorted_meses[-1]
                
                # Se a lista não for contínua, o BETWEEN pode pegar coisa extra, 
                # mas filtramos depois ou confiamos que a UI manda range.
                # Melhor filtrar explicitamente com IN se forem poucos, ou BETWEEN se for range.
                # Como a UI manda seleção, vamos usar IN para segurança exata, 
                # ou _TABLE_SUFFIX in (...) se a lista for pequena, 
                # ou _TABLE_SUFFIX BETWEEN ... se for grande.
                
                # Para simplificar e segurança: Construir string SQL
                # _TABLE_SUFFIX IN ('2026_01', '2026_02')
                suffixes = [f"'{m}'" for m in lista_meses]
                in_clause = ", ".join(suffixes)
                
                client = get_bq_client()
                if client:
                    query = f"""
                        SELECT * 
                        FROM `{settings.BQ_PROJECT}.{settings.BQ_DATASET}.atendimentos_*`
                        WHERE _TABLE_SUFFIX IN ({in_clause})
                    """
                    df = client.query(query).to_dataframe()
                    
                    if not df.empty:
                        # Remap columns
                        df.rename(columns={
                            "Atendido_por": "Atendido por",
                            "Nome_Cliente": "Nome Cliente",
                            "Data_Inicio": "Data Início"
                        }, inplace=True)
                        
                        # Processamento padrão
                        df = aplicar_depara(df)
                        if "Data" in df.columns:
                            df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors="coerce")
                            if df["Data"].dt.tz is not None:
                                df["Data"] = df["Data"].dt.tz_localize(None)
                            df["Dia"] = df["Data"].dt.date
                            df = df.sort_values(by="Data", ascending=False)
                            
                        return df
            except Exception as e:
                print(f"Erro no BQ Wildcard: {e}")
                # Fallback para loop individual se der erro no BQ

    # Fallback: Carrega um por um e concatena (Local ou erro no BQ)
    dfs = []
    for mes in lista_meses:
        # Tenta carregar como BQ individual ou Local
        # carregar_dados_mes aceita "BQ:2026_01" ou caminho
        # Vamos tentar inferir. Se estamos aqui, ou não tem BQ ou deu erro.
        # Tenta achar arquivo local correspondente
        ident = f"BQ:{mes}" if HAS_BQ else f"{mes}.csv"
        d = carregar_dados_mes(ident)
        if d is None and HAS_BQ: 
            # Se falhou como BQ, tenta local files mesmo com HAS_BQ true
             d = carregar_dados_mes(f"{mes}.csv")
             
        if d is not None:
            dfs.append(d)
            
    if dfs:
        return pd.concat(dfs, ignore_index=True)
        
    return None

