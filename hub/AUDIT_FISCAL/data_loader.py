from google.cloud import bigquery
from datetime import datetime


class BigQueryLoader:
    # MUDANÇA AQUI: Adicionamos o parâmetro 'credentials'
    def __init__(self, table_full_id, credentials):
        # Ex: "seu-projeto.auditoria_fiscal.registros_auditoria"
        self.table_id = table_full_id
        # MUDANÇA AQUI: Passamos as credentials para o Client
        self.client = bigquery.Client(credentials=credentials)

    def insert_record(self, record_dict):
        """
        Insere uma linha no BigQuery via Streaming (insert_rows_json).
        Retorna True se sucesso, False se falha.
        """
        # Adiciona timestamp de processamento se não existir
        if 'data_processamento' not in record_dict:
            record_dict['data_processamento'] = datetime.now().isoformat()

        # O BigQuery espera uma lista de linhas
        rows_to_insert = [record_dict]

        try:
            errors = self.client.insert_rows_json(self.table_id, rows_to_insert)

            if errors == []:
                print(f"✅ [BQ] Registro salvo com sucesso: {record_dict.get('nome_arquivo')}")
                return True
            else:
                print(f"❌ [BQ] Erro ao inserir: {errors}")
                return False

        except Exception as e:
            print(f"❌ [BQ] Erro Crítico na conexão: {e}")
            return False