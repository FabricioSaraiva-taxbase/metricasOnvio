
import os
import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account

# Add path to find config
sys.path.insert(0, os.path.join(os.getcwd(), 'AUDIT_FISCAL'))
try:
    from config import BQ_TABLE_ID
except ImportError:
    BQ_TABLE_ID = 'auditor-processos.auditoria_fiscal.registros_auditoria'

KEY_FILE = os.path.join(os.getcwd(), 'AUDIT_FISCAL', 'credentials.json')

def test_bq_efd_logic():
    print(f"Testing EFD Logic on table: {BQ_TABLE_ID}")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            KEY_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        client = bigquery.Client(credentials=creds)
        
        # Simula seleção de Fev/2026 (Auditoria) -> Periodo Ref = Jan/2026
        competencia = "01/2026"
        
        # Calc EFD = Dez/2025
        dt_selecionada = datetime.strptime(competencia, "%m/%Y")
        dt_efd = dt_selecionada.replace(day=1) - timedelta(days=1)
        dt_efd = dt_efd.replace(day=1)
        periodo_efd = dt_efd.strftime("%m/%Y")
        
        print(f"Simulação: Selecionado='{competencia}', EFD='{periodo_efd}'")

        query = f"""
            SELECT categoria, periodo, COUNT(*) as count 
            FROM `{BQ_TABLE_ID}` 
            WHERE (
                (periodo = '{competencia}' AND categoria != 'EFD_CONTRIBUICOES')
                OR
                (periodo = '{periodo_efd}' AND categoria = 'EFD_CONTRIBUICOES')
            )
            GROUP BY categoria, periodo
        """
        
        print("\n--- Executing Query ---")
        df = client.query(query).to_dataframe()
        print(df)
        
        # Validação
        has_std = not df[df['periodo'] == competencia].empty
        has_efd = not df[(df['periodo'] == periodo_efd) & (df['categoria'] == 'EFD_CONTRIBUICOES')].empty
        
        if has_std: print("✅ Found Standard records for 01/2026")
        else: print("⚠️ No Standard records for 01/2026 (Expected if DB empty)")
        
        if has_efd: print("✅ Found EFD records for 12/2025")
        else: print("⚠️ No EFD records for 12/2025 (Expected if DB empty)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bq_efd_logic()
