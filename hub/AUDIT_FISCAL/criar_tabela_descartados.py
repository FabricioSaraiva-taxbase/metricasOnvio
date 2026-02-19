from google.oauth2 import service_account
from google.cloud import bigquery

creds = service_account.Credentials.from_service_account_file(
    'credentials.json', scopes=['https://www.googleapis.com/auth/cloud-platform'])
client = bigquery.Client(credentials=creds)

# Recriar a tabela com data_processamento para identificar registros individuais
query = """
DROP TABLE IF EXISTS `auditor-processos.auditoria_fiscal.controle_descartados`
"""
client.query(query).result()

query = """
CREATE TABLE `auditor-processos.auditoria_fiscal.controle_descartados` (
    id_arquivo STRING NOT NULL,
    data_processamento TIMESTAMP,
    nome_arquivo STRING,
    data_descarte TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
"""
client.query(query).result()
print("Tabela controle_descartados recriada com data_processamento!")
