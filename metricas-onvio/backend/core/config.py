"""
Configurações centralizadas do Backend via variáveis de ambiente.
Usa pydantic-settings para validação e defaults seguros.
"""

import os
import secrets
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da aplicação. Podem ser overridden via variáveis de ambiente."""

    # --- JWT ---
    # Default = mesma SECRET_KEY do Hub Taxbase para aceitar tokens do Hub.
    # Em produção, definir via variável de ambiente TAXBASE_SECRET_KEY.
    SECRET_KEY: str = "taxbase-hub-secret-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas

    # --- Hub Integration ---
    HUB_URL: str = "http://localhost:5000"

    # --- BigQuery ---
    BQ_PROJECT: str = "taxbase-metricasmessenger"
    BQ_DATASET: str = "metricas"

    # --- Caminhos de Dados ---
    # Todos relativos à raiz do projeto (um nível acima de backend/)
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    MAPPING_FILE: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "statusContatos.xlsx")
    LABELS_JSON_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "month_labels.json")
    DEPARTMENTS_JSON_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "departments.json")
    SERVICE_ACCOUNT_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "service_account.json")

    # --- Credenciais Provisórias (mesmo do Streamlit) ---
    # Futuramente serão substituídas pelo SSO da Taxbase
    DEFAULT_PASSWORD: str = "taxbase123"

    model_config = {"env_prefix": "TAXBASE_"}


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância singleton das configurações."""
    return Settings()
