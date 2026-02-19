from google.cloud import bigquery
import os

PROJECT_ID = "taxbasehub"
DATASET_ID = "hub_dados"
TABLE_FUNCOES = f"{PROJECT_ID}.{DATASET_ID}.funcoes"

def fix_admin_role():
    client = bigquery.Client(project=PROJECT_ID)
    
    print(f"🔧 Verificando função 'admin_master' em {TABLE_FUNCOES}...")
    
    query_check = f"SELECT * FROM `{TABLE_FUNCOES}` WHERE id = 'admin_master'"
    results = client.query(query_check).to_dataframe()
    
    if results.empty:
        print("⚠️ Função 'admin_master' NÃO encontrada (Isso causa o erro!).")
        print("🛠️ Criando função 'admin_master' agora...")
        
        # Inserir função admin_master
        # Nota: 'sistemas' é um ARRAY<STRING> no BigQuery
        query_insert = f"""
            INSERT INTO `{TABLE_FUNCOES}` (id, nome, permissao, sistemas, `desc`)
            VALUES ('admin_master', 'Super Admin', 'admin', ['*'], 'Acesso total ao sistema')
        """
        try:
            client.query(query_insert).result()
            print("✅ Função 'admin_master' criada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar função: {e}")
    else:
        print("✅ Função 'admin_master' JÁ EXISTE.")
        print(results)

if __name__ == "__main__":
    fix_admin_role()
