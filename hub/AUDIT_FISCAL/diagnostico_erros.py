import pandas as pd
import re
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Importa seus módulos
from config import BQ_TABLE_ID
from content_extractor import ContentExtractor
from reference_data import ReferenceLoader

KEY_FILE = 'credentials.json'


def get_credentials():
    return service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=['https://www.googleapis.com/auth/drive',
                          'https://www.googleapis.com/auth/spreadsheets',
                          'https://www.googleapis.com/auth/cloud-platform']
    )


def main():
    print("🕵️ INICIANDO DIAGNÓSTICO DE ARQUIVOS NÃO IDENTIFICADOS...")
    creds = get_credentials()

    # 1. Carregar a Memória (Planilha) para saber o que temos cadastrado
    ref_loader = ReferenceLoader(creds)
    ref_loader.load_data()

    # 2. Conectar no BigQuery e pegar os erros
    client = bigquery.Client(credentials=creds)

    # Pega os últimos 20 erros para não demorar muito
    query = f"""
        SELECT id_arquivo, nome_arquivo, link_arquivo
        FROM `{BQ_TABLE_ID}`
        WHERE cnpj = 'NAO_DETECTADO' 
           OR cnpj = 'NAO_IDENTIFICADO'
        ORDER BY data_processamento DESC
        LIMIT 20
    """

    df_erros = client.query(query).to_dataframe()

    if df_erros.empty:
        print("✅ Maravilha! Não há arquivos 'NAO_DETECTADO' no BigQuery recentemente.")
        return

    print(f"⚠️ Encontrados {len(df_erros)} arquivos problemáticos. Analisando um por um...\n")

    # Prepara o extrator
    service_drive = build('drive', 'v3', credentials=creds)
    extractor = ContentExtractor(service_drive, creds)

    for i, row in df_erros.iterrows():
        file_id = row['id_arquivo']
        file_name = row['nome_arquivo']

        print(f"--- 📄 Analisando: {file_name} ---")
        print(f"    🔗 Link: {row['link_arquivo']}")

        # Refaz a extração
        texto, cnpj_extraido, usou_ocr = extractor.process_file(file_id, file_name)

        # Limpa o texto para facilitar leitura no log
        texto_limpo = " ".join(texto.split()) if texto else ""

        print(f"    👁️ Usou OCR? {'SIM' if usou_ocr else 'NÃO (Texto Direto)'}")
        print(f"    📝 Texto Extraído (Primeiros 200 caracteres):")
        print(f"       [{texto_limpo[:200]}...]")

        # Análise Forense
        # Procura qualquer sequência de números que pareça CNPJ (14), IE ou IM (acima de 6 digitos)
        numeros_achados = re.findall(r'\d{6,14}', texto_limpo.replace('.', '').replace('/', '').replace('-', ''))

        encontrou_match = False

        print(f"    🔍 Números encontrados no documento: {numeros_achados[:10]}...")  # Mostra só os 10 primeiros

        for num in numeros_achados:
            # Verifica se esse número existe na nossa base (mesmo que o robô não tenha pego antes)
            if num in ref_loader.fast_lookup:
                empresa = ref_loader.fast_lookup[num]
                print(f"    ✅ MATCH ENCONTRADO NA BASE! O número {num} pertence a:")
                print(f"       🏢 {empresa['empresa']} (CNPJ: {empresa['cnpj']})")
                encontrou_match = True
                break

        if not encontrou_match:
            print("    ❌ NENHUM número do documento bateu com a planilha.")
            print("       -> Hipótese 1: O CNPJ/IM deste cliente não está na planilha.")
            print("       -> Hipótese 2: O OCR leu o número errado (ex: leu 'O' em vez de '0').")
        else:
            print("    ⚠️ O número está na planilha, mas o script principal falhou.")
            print("       -> Hipótese: O regex principal pode estar muito restrito.")

        print("-" * 50)


if __name__ == "__main__":
    main()