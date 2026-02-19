
import json
import os
from typing import Dict
from backend.core.config import get_settings
from backend.services.bigquery_service import get_bq_client

TABLE_ID = "metricas.config_departments"

def _load_departments_json() -> Dict[str, str]:
    """Carrega departamentos do arquivo JSON local."""
    settings = get_settings()
    path = settings.DEPARTMENTS_JSON_PATH

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_departments_json(departments: Dict[str, str]) -> None:
    """Salva departamentos no arquivo JSON local."""
    settings = get_settings()
    path = settings.DEPARTMENTS_JSON_PATH

    # Garante que o diretório exista se necessário, mas aqui estamos na raiz do projeto
    with open(path, "w", encoding="utf-8") as f:
        json.dump(departments, f, ensure_ascii=False, indent=2)

def load_departments() -> Dict[str, str]:
    """Retorna o mapeamento atual de Analista -> Departamento. Prioriza BigQuery."""
    # Tenta BigQuery
    try:
        client = get_bq_client()
        if client:
            query = f"SELECT analyst, department FROM `{client.project}.{TABLE_ID}`"
            df = client.query(query).to_dataframe()
            return dict(zip(df["analyst"], df["department"]))
    except Exception as e:
        print(f"Error loading departments from BQ: {e}")

    # Fallback Local
    return _load_departments_json()

def save_department_mapping(mapping: Dict[str, str]) -> bool:
    """
    Salva o mapeamento completo de departamentos.
    Atualiza BigQuery e JSON local.
    """
    try:
        # 1. Update Local JSON (Backup/Fallback)
        current = _load_departments_json()
        current.update(mapping)
        _save_departments_json(current)

        # 2. Update BigQuery
        client = get_bq_client()
        if client:
            # For full mapping update, easiest strategy is Truncate + Insert
            # (Assuming `mapping` contains the FULL state intended, or partial?)
            # The UI logic suggests we might be sending updates.
            # But here `mapping` argument implies a dict.
            # If we want to support partial updates safely in BQ without transaction complexity:
            # We can iterate and UPSERT or just DELETE/INSERT one by one if small.
            # But typically this function is used for bulk save?
            # Let's assume bulk replace if the intention is "Save Configuration".
            # If the UI sends only changes, we should use update_single_analyst loop.
            
            # Implementation for `update_single_analyst` handles one by one.
            # If this function is called, it might be a bulk import.
            # Let's implement Upsert logic:
            # MERGE INTO table T USING (SELECT * FROM UNNEST(...)) S ON T.analyst = S.analyst ...
            
            # Construct rows
            rows = [{"analyst": k, "department": v} for k, v in mapping.items()]
            if not rows:
                return True

            # Use MERGE query for atomic upsert
            # We need to construct a temporary table or use UNNEST with detailed typing.
            # Easier: Delete existing for these analysts and Insert new.
            
            keys = [f"'{k}'" for k in mapping.keys()]
            if keys:
                keys_str = ", ".join(keys)
                # Delete
                query_del = f"DELETE FROM `{client.project}.{TABLE_ID}` WHERE analyst IN ({keys_str})"
                client.query(query_del).result()
                
                # Insert
                errors = client.insert_rows_json(f"{client.project}.{TABLE_ID}", rows)
                if errors:
                    print(f"BQ Insert Errors: {errors}")

        return True
    except Exception as e:
        print(f"Error saving to BQ: {e}")
        return False

def update_single_analyst(analyst: str, department: str) -> bool:
    """Atualiza ou insere o departamento de um analista específico."""
    try:
        # 1. Update Local
        current = _load_departments_json()
        if not department:
            current.pop(analyst, None)
        else:
            current[analyst] = department
        _save_departments_json(current)

        # 2. Update BigQuery
        client = get_bq_client()
        if client:
            if not department:
                # Delete
                query = f"DELETE FROM `{client.project}.{TABLE_ID}` WHERE analyst = '{analyst}'"
                client.query(query).result()
            else:
                # Merge (Upsert)
                # Safe logic: Delete then Insert
                query = f"DELETE FROM `{client.project}.{TABLE_ID}` WHERE analyst = '{analyst}'"
                client.query(query).result()
                
                row = {"analyst": analyst, "department": department}
                client.insert_rows_json(f"{client.project}.{TABLE_ID}", [row])

        return True
    except Exception as e:
        print(f"Error updating BQ: {e}")
        return False
