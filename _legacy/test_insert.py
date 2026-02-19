
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

print("Imports starting...", flush=True)
from backend.services.bigquery_service import get_bq_client
from backend.core.config import get_settings
from datetime import datetime
print("Imports done.", flush=True)

def test_insert():
    print("Getting client...", flush=True)
    client = get_bq_client()
    settings = get_settings()

    
    # Logic from mapping_service.py
    TABLE_ID = "metricas.config_client_mapping"
    full_table_id = f"{client.project}.{TABLE_ID}"
    
    import pandas as pd
    from google.cloud import bigquery

    print(f"Target Table: {full_table_id}")
    
    row = {
        "original_name": "TEST_CONTACT_LOAD", 
        "normalized_name": "TEST_CLIENT_LOAD",
        "updated_at": datetime.utcnow().isoformat()
    }
    
    df = pd.DataFrame([row])
    df["updated_at"] = pd.to_datetime(df["updated_at"])
    
    print(f"Loading dataframe: {df}")
    print(f"Dtypes: {df.dtypes}")

    
    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
        )
        job = client.load_table_from_dataframe(df, full_table_id, job_config=job_config)
        job.result()
        print("Load Job success!")
    except Exception as e:
        print(f"Exception during load: {e}")


if __name__ == "__main__":
    test_insert()
