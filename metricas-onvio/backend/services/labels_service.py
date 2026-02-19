"""
Serviço de labels de meses (híbrido BigQuery + JSON local).
Portado de app_metricas.py (linhas 891-958).
"""

import json
import os
from typing import Dict, Tuple

from backend.core.config import get_settings
from backend.core.config import get_settings
from backend.services.bigquery_service import get_bq_client

TABLE_ID = "metricas.config_labels"


def _load_labels_json() -> Dict[str, str]:
    """Carrega labels do arquivo JSON local."""
    settings = get_settings()
    path = settings.LABELS_JSON_PATH

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_labels_json(labels: Dict[str, str]) -> None:
    """Salva labels no arquivo JSON local."""
    settings = get_settings()
    path = settings.LABELS_JSON_PATH

    with open(path, "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)


def load_month_labels() -> Dict[str, str]:
    """
    Carrega labels dos meses.
    Mescla BigQuery + JSON local (BQ tem prioridade).
    """
    # Base: JSON local (Fallback)
    labels = _load_labels_json()

    # Tenta complementar/sobrescrever com BigQuery
    try:
        client = get_bq_client()
        if client:
            query = (
                f"SELECT mes_key, label "
                f"FROM `{client.project}.{TABLE_ID}` "
                "WHERE label IS NOT NULL AND label != ''"
            )
            df = client.query(query).to_dataframe()
            bq_labels = dict(zip(df["mes_key"], df["label"]))
            labels.update(bq_labels)  # BQ sobrescreve JSON para mesmas chaves
    except Exception as e:
        print(f"Error loading labels from BQ: {e}")

    return labels


def save_month_label(mes_key: str, label: str) -> Tuple[bool, str]:
    """
    Salva label de um mês.
    Tenta BigQuery primeiro; se falhar (billing), faz fallback para JSON local.
    """
    # Tenta BigQuery primeiro
    try:
        client = get_bq_client()
        if client:
            query_del = (
                f"DELETE FROM `{client.project}.{TABLE_ID}` "
                f"WHERE mes_key = '{mes_key}'"
            )
            client.query(query_del).result()

            if label.strip():
                label_safe = label.replace("'", "\\'")
                ins_query = (
                    f"INSERT INTO `{client.project}.{TABLE_ID}` "
                    f"(mes_key, label, updated_at) VALUES ('{mes_key}', '{label_safe}', CURRENT_TIMESTAMP())"
                )
                client.query(ins_query).result()

            # Also update local for consistency/fallback
            # Fallback block below does it if BQ fails, but we should do it anyway?
            # Or just rely on BQ success?
            # Let's keep local updated as backup.
            _update_local_json(mes_key, label)
            
            return True, "BigQuery"
    except Exception as e:
         print(f"BQ Save error: {e}")
         # Continue to fallback

    # Fallback: JSON local
    try:
        _update_local_json(mes_key, label)
        return True, "JSON local"
    except Exception as e:
        return False, str(e)

def _update_local_json(mes_key: str, label: str):
    labels = _load_labels_json()
    if label.strip():
        labels[mes_key] = label
    else:
        labels.pop(mes_key, None)
    _save_labels_json(labels)
