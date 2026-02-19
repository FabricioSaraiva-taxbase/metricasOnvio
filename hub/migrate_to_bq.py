
import os
import json
from google.cloud import bigquery
from google.oauth2 import service_account

# Configuração
PROJECT_ID = "taxbasehub"
DATASET_ID = "hub_dados"
LOCATION = "southamerica-east1"

# Caminhos dos arquivos
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
FILES = {
    "usuarios": os.path.join(DATA_DIR, 'usuarios.json'),
    "sistemas": os.path.join(DATA_DIR, 'sistemas.json'),
    "funcoes": os.path.join(DATA_DIR, 'funcoes.json')
}

# Schemas
SCHEMAS = {
    "usuarios": [
        bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("nome", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("funcao_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("senha", "STRING", mode="REQUIRED"), 
    ],
    "sistemas": [
        bigquery.SchemaField("sistema_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("nome", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("url", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("categoria", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("desc", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status_manual", "STRING", mode="NULLABLE"),
    ],
    "funcoes": [
        bigquery.SchemaField("id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("nome", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("sistemas", "STRING", mode="REPEATED"), 
        bigquery.SchemaField("permissao", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("descricao", "STRING", mode="NULLABLE"),
    ]
}

def get_client():
    # MODIFICADO: Ignora credentials.json local para forçar uso do login do usuário (gcloud)
    # Isso resolve o conflito de permissão se o JSON for de outro projeto (auditor-processos)
    
    # key_path = os.path.join(os.path.dirname(__file__), 'AUDIT_FISCAL', 'credentials.json')
    # if os.path.exists(key_path):
    #     creds = service_account.Credentials.from_service_account_file(key_path)
    #     return bigquery.Client(project=PROJECT_ID, credentials=creds)
    
    print("🔑 Usando credenciais do sistema (gcloud)...")
    return bigquery.Client(project=PROJECT_ID)

def create_dataset(client):
    dataset_id = f"{PROJECT_ID}.{DATASET_ID}"
    try:
        client.get_dataset(dataset_id)
        print(f"✅ Dataset {dataset_id} já existe.")
    except Exception:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = LOCATION
        dataset = client.create_dataset(dataset, timeout=30) 
        print(f"✅ Dataset {dataset_id} criado.")

def migrate_table(client, table_name, file_path, schema):
    if not os.path.exists(file_path):
        print(f"⚠️ Arquivo {file_path} não encontrado. Pulando {table_name}.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data:
        print(f"⚠️ Arquivo {file_path} vazio. Pulando {table_name}.")
        return

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    
    # Configurar Job
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE", # Sobrescreve a tabela
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    # Carregar dados
    try:
        job = client.load_table_from_json(data, table_id, job_config=job_config)
        job.result() # Aguarda processamento
        print(f"✅ Tabela {table_name} migrada com {len(data)} registros.")
    except Exception as e:
        print(f"❌ Erro ao migrar {table_name}: {e}")

def main():
    print("🚀 Iniciando migração para BigQuery...")
    client = get_client()
    create_dataset(client)

    for name, file_path in FILES.items():
        migrate_table(client, name, file_path, SCHEMAS[name])

    print("🏁 Migração concluída!")

if __name__ == "__main__":
    main()
