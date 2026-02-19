
import os
import sys
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.core.config import get_settings
from backend.services.bigquery_service import get_bq_client

def migrate_mapping():
    settings = get_settings()
    client = get_bq_client()
    
    if not client:
        print("❌ Could not create BigQuery client. Check credentials.")
        return

    table_id = f"{settings.BQ_PROJECT}.{settings.BQ_DATASET}.config_client_mapping"
    xlsx_path = settings.MAPPING_FILE
    
    if not os.path.exists(xlsx_path):
        print(f"⚠️ {xlsx_path} not found. Nothing to migrate.")
        return

    # Load Excel
    try:
        df_map = pd.read_excel(xlsx_path, engine="openpyxl")
    except Exception as e:
        print(f"❌ Error reading Excel: {e}")
        return

    # Normalize Columns
    cols_map = {c.upper(): c for c in df_map.columns}
    if "NOME DO CONTATO" not in cols_map or "NOME CLIENTE" not in cols_map:
        print("❌ Required columns 'NOME DO CONTATO' and 'NOME CLIENTE' not found.")
        return

    df_clean = df_map[[cols_map["NOME DO CONTATO"], cols_map["NOME CLIENTE"]]].copy()
    df_clean.columns = ["original_name", "normalized_name"]
    
    # Clean data
    df_clean["original_name"] = df_clean["original_name"].astype(str).str.strip().str.upper()
    df_clean["normalized_name"] = df_clean["normalized_name"].astype(str).str.strip()
    
    # Remove duplicates on original_name
    df_clean = df_clean.drop_duplicates(subset=["original_name"])
    
    # Remove empty
    df_clean = df_clean[df_clean["original_name"] != "NAN"]
    df_clean = df_clean[df_clean["original_name"] != ""]
    
    print(f"📂 Loaded {len(df_clean)} mappings from Excel.")

    # Create Table
    schema = [
        bigquery.SchemaField("original_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("normalized_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.get_table(table_id)
        print(f"✅ Table {table_id} already exists.")
    except NotFound:
        client.create_table(table)
        print(f"✅ Created table {table_id}.")

    # Prepare rows
    rows_to_insert = []
    now = datetime.utcnow().isoformat()
    
    for _, row in df_clean.iterrows():
        rows_to_insert.append({
            "original_name": row["original_name"],
            "normalized_name": row["normalized_name"],
            "updated_at": now
        })

    if rows_to_insert:
        # Use Load Job with WRITE_TRUNCATE
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            schema=schema
        )
        
        try:
            job = client.load_table_from_json(
                rows_to_insert, 
                table_id, 
                job_config=job_config
            )
            job.result()
            print(f"✅ Migration complete. {len(rows_to_insert)} total rows.")
        except Exception as e:
            print(f"❌ Load Job Error: {e}")

if __name__ == "__main__":
    migrate_mapping()
