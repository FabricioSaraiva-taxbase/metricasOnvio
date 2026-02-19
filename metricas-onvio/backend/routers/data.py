"""
Router de Dados.
GET /api/data/list_months → lista meses disponíveis.
GET /api/data/get_month/{month_id} → retorna dados processados de um mês.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import io

from backend.core.auth import get_current_user
from backend.models.schemas import KPIs, MonthDataResponse, MonthItem, MonthListResponse, PeriodRequest
from backend.services.data_service import carregar_dados_mes, listar_arquivos_por_ano, carregar_periodo_meses

router = APIRouter(prefix="/api/data", tags=["Dados"])


@router.get("/list_months", response_model=MonthListResponse)
async def list_months(current_user: dict = Depends(get_current_user)):
    """
    Lista todos os meses disponíveis, agrupados por ano.
    Suporta BigQuery (nuvem) e CSVs locais.
    """
    try:
        estrutura = listar_arquivos_por_ano()

        # Converte para o schema Pydantic
        data = {}
        for ano, meses in estrutura.items():
            data[ano] = [
                MonthItem(
                    caminho=m["caminho"],
                    display=m["display"],
                    mes_raw=m["mes_raw"],
                )
                for m in meses
            ]

        return MonthListResponse(data=data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar meses: {str(e)}",
        )


@router.get("/get_month/{month_id:path}", response_model=MonthDataResponse)
async def get_month(month_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retorna os dados processados de um mês específico.

    Args:
        month_id: Identificador do mês. Exemplos:
            - 'BQ:2026_01' (BigQuery)
            - 'data/2026_01.csv' (CSV local)
    """
    try:
        df = carregar_dados_mes(month_id)

        if df is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dados não encontrados para: {month_id}",
            )

        # Calcula KPIs (mesma lógica do renderizar_metricas_limpas)
        excluir = ["TAXBASE INTERNO", "IGNORAR", "NÃO IDENTIFICADO"]
        df_ranking = df[~df["Cliente_Final"].isin(excluir)]

        kpis = KPIs(
            total_bruto=len(df),
            total_validos=len(df_ranking),
            clientes_unicos=int(df_ranking["Cliente_Final"].nunique()),
        )

        # Converte DataFrame para lista de dicts (serialização JSON)
        # Trata tipos não-serializáveis (datetime, date, NaN)
        records = df.where(df.notnull(), None).to_dict(orient="records")
        for record in records:
            for key, value in record.items():
                if hasattr(value, "isoformat"):
                    record[key] = value.isoformat()

        return MonthDataResponse(
            total_records=len(df),
            columns=list(df.columns),
            records=records,
            kpis=kpis,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar dados: {str(e)}",
        )


@router.get("/download_month/{month_id:path}")
async def download_month(month_id: str, current_user: dict = Depends(get_current_user)):
    """
    Retorna um arquivo CSV com os dados do mês.
    """
    try:
        # Carrega DataFrame
        df = carregar_dados_mes(month_id)

        if df is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dados não encontrados para: {month_id}",
            )

        # Converte para CSV na memória (separador ;)
        stream = io.StringIO()
        df.to_csv(stream, index=False, sep=";")
        
        # Prepara resposta de download
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        filename = f"relatorio_{month_id.replace(':', '_').replace('/', '-')}.csv"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        
        return response

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar CSV: {str(e)}",
        )


@router.post("/get_period", response_model=MonthDataResponse)
async def get_period(request: PeriodRequest, current_user: dict = Depends(get_current_user)):
    """
    Retorna dados agregados de múltiplos meses.
    Otimizado para reduzir round-trips e usar consultas eficientes no BQ.
    """
    try:
        df = carregar_periodo_meses(request.months)

        if df is None or df.empty:
            # Retorna estrutura vazia em vez de erro 404 para periodos
            return MonthDataResponse(
                total_records=0,
                columns=[],
                records=[],
                kpis=KPIs(total_bruto=0, total_validos=0, clientes_unicos=0)
            )

        # Calcula KPIs
        excluir = ["TAXBASE INTERNO", "IGNORAR", "NÃO IDENTIFICADO"]
        df_ranking = df[~df["Cliente_Final"].isin(excluir)]

        kpis = KPIs(
            total_bruto=len(df),
            total_validos=len(df_ranking),
            clientes_unicos=int(df_ranking["Cliente_Final"].nunique()),
        )

        # Serialização
        records = df.where(df.notnull(), None).to_dict(orient="records")
        for record in records:
            for key, value in record.items():
                if hasattr(value, "isoformat"):
                    record[key] = value.isoformat()

        return MonthDataResponse(
            total_records=len(df),
            columns=list(df.columns),
            records=records,
            kpis=kpis,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao carregar período: {str(e)}",
        )
