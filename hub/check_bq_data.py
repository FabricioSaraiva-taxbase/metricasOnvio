from google.cloud import bigquery
import hashlib

PROJECT_ID = "taxbasehub"
DATASET_ID = "hub_dados"
TABLE_USUARIOS = f"{PROJECT_ID}.{DATASET_ID}.usuarios"

def check_data():
    print(f"🔍 Verificando tabela: {TABLE_USUARIOS}...")
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # 1. Verificar se tabela existe e tem dados
        query = f"SELECT * FROM `{TABLE_USUARIOS}` LIMIT 5"
        results = client.query(query).to_dataframe()
        
        if results.empty:
            print("❌ ERRO: A tabela existe mas está VAZIA. A migração não inseriu os dados.")
            return False
            
        print(f"✅ SUCESSO! Encontrados {len(results)} usuários.")
        print(results[['email', 'nome', 'funcao_id']])
        
        # 2. Listar TODOS os usuários para conferência
        print("\n📋 Lista de Usuários no BigQuery:")
        for row in results.to_dict('records'):
            print(f"- {row['email']} (Função: {row['funcao_id']}) | Hash: {row['senha'][:10]}...")
            
        return True

            
        return True

    except Exception as e:
        print(f"❌ ERRO CRÍTICO ao conectar: {e}")
        return False

if __name__ == "__main__":
    check_data()
