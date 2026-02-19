
from backend.services.bigquery_service import get_bq_client
from backend.core.config import get_settings

def debug():
    client = get_bq_client()
    settings = get_settings()
    table_id = f"{settings.BQ_PROJECT}.{settings.BQ_DATASET}.config_client_mapping"
    
    print(f"Checking table: {table_id}")
    
    # 1. Check Schema
    try:
        table = client.get_table(table_id)
        print("Schema:")
        for field in table.schema:
            print(f" - {field.name} ({field.field_type})")
            
    except Exception as e:
        print(f"Error getting table: {e}")
        return

    # 2. Check Recent Rows
    print("\nRecent Rows:")
    try:
        query = f"SELECT * FROM `{table_id}` ORDER BY updated_at DESC LIMIT 10"
        df = client.query(query).to_dataframe()
        print(df)
    except Exception as e:
        print(f"Error querying rows: {e}")

    # 3. Check Duplicates
    print("\nCheck Duplicates (Top 5):")
    try:
        query = f"""
        SELECT original_name, COUNT(*) as qtd 
        FROM `{table_id}` 
        GROUP BY original_name 
        HAVING qtd > 1 
        ORDER BY qtd DESC 
        LIMIT 5
        """
        df_dup = client.query(query).to_dataframe()
        print(df_dup)
    except Exception as e:
        print(f"Error checking dups: {e}")


if __name__ == "__main__":
    debug()
