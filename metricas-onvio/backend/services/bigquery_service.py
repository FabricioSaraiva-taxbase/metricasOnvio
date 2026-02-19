"""
Serviço de conexão com o BigQuery.
Portado de app_metricas.py (linhas 12-40), removendo dependência do Streamlit.
"""

import os
from typing import Optional

HAS_BQ = False
_bq_client = None

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account as sa_module

    HAS_BQ = True
except ImportError:
    HAS_BQ = False


def get_bq_client(service_account_path: Optional[str] = None) -> Optional["bigquery.Client"]:
    """
    Retorna cliente BigQuery autenticado via service_account.json.
    Usa cache em módulo para evitar recriação a cada chamada.
    """
    global _bq_client

    if not HAS_BQ:
        return None

    if _bq_client is not None:
        return _bq_client

    try:
        # Resolve o caminho do arquivo de credenciais
        if service_account_path is None:
            from backend.core.config import get_settings
            service_account_path = get_settings().SERVICE_ACCOUNT_PATH

        if os.path.exists(service_account_path):
            creds = sa_module.Credentials.from_service_account_file(service_account_path)
            _bq_client = bigquery.Client(credentials=creds, project=creds.project_id)
            return _bq_client

        # Fallback: variável de ambiente GOOGLE_APPLICATION_CREDENTIALS
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            _bq_client = bigquery.Client()
            return _bq_client
            
        # Fallback 2: Default Credentials (ADC) - Cloud Run / Local GCloud Auth
        try:
            from backend.core.config import get_settings
            project_id = get_settings().BQ_PROJECT
            _bq_client = bigquery.Client(project=project_id)
            return _bq_client
        except Exception as e:
            # Fallback 3: No Project arg (last resort)
            try:
                print(f"DEBUG BQ Client Init (with project) failed: {e}. Trying without.")
                _bq_client = bigquery.Client()
                return _bq_client
            except:
                pass

        return None

    except Exception:
        return None


def is_bigquery_available() -> bool:
    """Verifica se o BigQuery está disponível e acessível."""
    if not HAS_BQ:
        return False
    client = get_bq_client()
    return client is not None
