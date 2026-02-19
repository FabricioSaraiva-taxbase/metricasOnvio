
import json
import os
import sys
from datetime import datetime
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.core.config import get_settings
from backend.services.bigquery_service import get_bq_client

def migrate_labels():
    settings = get_settings()
    client = get_bq_client()
    
    if not client:
        print("❌ Could not create BigQuery client. Check credentials.")
        return

    # Use config_labels instead of month_labels to be consistent with plan
    table_id = f"{settings.BQ_PROJECT}.{settings.BQ_DATASET}.config_labels"
    json_path = settings.LABELS_JSON_PATH
    
    if not os.path.exists(json_path):
        print(f"⚠️ {json_path} not found. Nothing to migrate.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"📂 Loaded {len(data)} labels from JSON.")

    # Create Table
    schema = [
        bigquery.SchemaField("mes_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("label", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.get_table(table_id)
        print(f"✅ Table {table_id} already exists.")
    except NotFound:
        client.create_table(table)
        print(f"✅ Created table {table_id}.")

    # Fetch existing to avoid overwrite/duplication if not needed, 
    # but for migration usually we want to ensure local is in BQ.
    # We will TRUNCATE and RELOAD to be safe and consistent with previous step.
    
    rows_to_insert = []
    now = datetime.utcnow().isoformat()
    for mes, label in data.items():
        rows_to_insert.append({
            "mes_key": mes,
            "label": label,
            "updated_at": now
        })

    if rows_to_insert:
        # Check if table has data.
        # If we truncate, we might lose data if BQ was ahead of JSON?
        # The service was hybrid: it attempted to load BQ first.
        # But if BQ had data that JSON didn't, truncating would lose it.
        # So filtering is better here.
        
        # 1. Get existing BQ data
        query = f"SELECT mes_key, label FROM `{table_id}`"
        try:
            df = client.query(query).to_dataframe()
            existing = dict(zip(df.mes_key, df.label))
        except:
            existing = {}

        # 2. Merge: Local overwrites BQ? or BQ overwrites Local?
        # Service `load_month_labels`: BQ overwrites JSON.
        # So BQ is the source of truth if it exists.
        # But if we want to "Migrate Local to BQ", we imply local has new info?
        # Assuming we want to UNION them.
        
        merged = {**existing, **data} # Local overwrite existing?
        # If the goal is "Make BQ the single source of truth based on current state":
        # Current state = local JSON + BQ.
        # So we should take the union.
        
        final_rows = []
        for mes, label in merged.items():
            final_rows.append({
                "mes_key": mes,
                "label": label,
                "updated_at": now
            })
            
            
        # Use Load Job with WRITE_TRUNCATE
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            schema=schema
        )
        
        try:
            job = client.load_table_from_json(
                final_rows, 
                table_id, 
                job_config=job_config
            )
            job.result()
            print(f"🚀 Migrated {len(final_rows)} labels (Merged JSON + Existing BQ).")
        except Exception as e:
            print(f"❌ Load Job Error: {e}")

if __name__ == "__main__":
    migrate_labels()
