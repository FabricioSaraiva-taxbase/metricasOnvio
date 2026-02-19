
import os
import sys
from google.cloud import bigquery
from google.oauth2 import service_account

# Add path to find config
sys.path.insert(0, os.path.join(os.getcwd(), 'AUDIT_FISCAL'))
try:
    from config import BQ_TABLE_ID
except ImportError:
    BQ_TABLE_ID = 'auditor-processos.auditoria_fiscal.registros_auditoria'

KEY_FILE = os.path.join(os.getcwd(), 'AUDIT_FISCAL', 'credentials.json')

def test_bq_period_filter():
    print(f"Testing BigQuery Filter on table: {BQ_TABLE_ID}")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        client = bigquery.Client(credentials=creds)
        
        # 1. Get available periods
        print("\n--- QUERYING DISTINCT PERIODOS ---")
        query_distinct = f"SELECT DISTINCT periodo FROM `{BQ_TABLE_ID}` ORDER BY periodo DESC LIMIT 10"
        rows = client.query(query_distinct).result()
        
        found_periods = []
        for row in rows:
            p = row.get('periodo')
            print(f"Found Period: '{p}'")
            if p: found_periods.append(p)
            
        if not found_periods:
            print("No periods found in BQ!")
            return

        # 2. Test filter with the first found period
        target = found_periods[0]
        print(f"\n--- Testing Filter: periodo = '{target}' ---")
        
        query_filter = f"SELECT COUNT(*) as cnt FROM `{BQ_TABLE_ID}` WHERE periodo = '{target}'"
        res = client.query(query_filter).result()
        for r in res:
            print(f"Count for '{target}': {r.cnt}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bq_period_filter()
