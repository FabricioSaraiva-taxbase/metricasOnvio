from google.cloud import bigquery
import os
import pandas as pd

# --- CONFIGURAÇÃO ---
# 1. Coloque o nome exato do seu arquivo json aqui
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"


def testar_conexao():
    print("Tentando conectar ao BigQuery...")

    # Cria o cliente
    client = bigquery.Client()

    # Exemplo: Testando Janeiro de 2026
    tabela = "atendimentos_2026_01"

    query = f"""
            SELECT * FROM `taxbase-metricasmessenger.metricas.{tabela}` 
            LIMIT 5
        """

    try:
        # Roda a query e joga num DataFrame do Pandas
        df = client.query(query).to_dataframe()

        print("\n✅ SUCESSO! Conexão estabelecida.")
        print(f"Foram baixadas {len(df)} linhas de teste.")
        print("Aqui estão as primeiras linhas:")
        print(df.head())

    except Exception as e:
        print("\n❌ ERRO NA CONEXÃO:")
        print(e)


if __name__ == "__main__":
    testar_conexao()