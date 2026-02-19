
import json
import os
import sys
from datetime import datetime
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.core.config import get_settings
from backend.services.bigquery_service import get_bq_client

def migrate_departments():
    settings = get_settings()
    client = get_bq_client()
    
    if not client:
        print("❌ Could not create BigQuery client. Check credentials.")
        return

    table_id = f"{settings.BQ_PROJECT}.{settings.BQ_DATASET}.config_departments"
    json_path = settings.DEPARTMENTS_JSON_PATH
    
    # 1. Load Local Data
    if not os.path.exists(json_path):
        print(f"⚠️ {json_path} not found. Nothing to migrate.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"📂 Loaded {len(data)} departments from JSON.")

    # 2. Create Table if not exists
    schema = [
        bigquery.SchemaField("analyst", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("department", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    try:
        client.get_table(table_id)
        print(f"✅ Table {table_id} already exists.")
    except NotFound:
        client.create_table(table)
        print(f"✅ Created table {table_id}.")

    # 3. Insert Data (Normalized)
    rows_to_insert = []
    now = datetime.utcnow().isoformat()
    
    # Deduplicate and Normalize
    normalized_data = {}
    for analyst, dept in data.items():
        key = analyst.strip().upper()
        # If duplicate, last one wins (or keep existing? local json order is arbitrary if dict)
        # We prefer "Uppercase" if available, but here we just upper everything.
        normalized_data[key] = dept
        
    for analyst, dept in normalized_data.items():
        rows_to_insert.append({
            "analyst": analyst,
            "department": dept,
            "updated_at": now
        })

    if rows_to_insert:
        # Use Load Job with WRITE_TRUNCATE instead of DML (TRUNCATE statement)
        # This works in BigQuery Sandbox (No Billing).
        
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
            job.result()  # Wait for completion
            print(f"🚀 Successfully migrated {len(rows_to_insert)} records to BigQuery (Load Job)!")
        except Exception as e:
            print(f"❌ Load Job Error: {e}")
    else:
        print("Empty dataset, nothing to insert.")

if __name__ == "__main__":
    migrate_departments()
