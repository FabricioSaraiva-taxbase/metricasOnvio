import os
import concurrent.futures
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import BQ_TABLE_ID
from drive_watcher import DriveWatcher
from content_extractor import ContentExtractor
from reference_data import ReferenceLoader
from data_loader import BigQueryLoader
from auditor_logic import AuditorClassifier

KEY_FILE = 'credentials.json'
MAX_WORKERS = 6  # Reduzi um pouco para evitar crash de memória no Windows


def get_credentials():
    return service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=['https://www.googleapis.com/auth/drive',
                          'https://www.googleapis.com/auth/spreadsheets',
                          'https://www.googleapis.com/auth/cloud-platform']
    )


def processar_arquivo_individual(file_meta, creds, ref_loader, classifier, ids_existentes):
    # Buffer de log para imprimir tudo de uma vez e não misturar as threads
    log_buffer = []
    file_name = file_meta['name']
    file_id = file_meta['id']

    # 0. BLACKLIST: Pula arquivos irrelevantes ANTES de qualquer processamento
    if classifier.is_blacklisted(file_name):
        log_buffer.append(f"⛔ [BLACKLIST] Ignorado: {file_name}")
        print("\n".join(log_buffer))
        print("-" * 40)
        return True  # Não é erro, apenas ignorado

    # 0.5. DUPLICADOS: Pula se já existe no BigQuery
    if file_id in ids_existentes:
        log_buffer.append(f"🔁 [DUPLICADO] Já processado: {file_name}")
        print("\n".join(log_buffer))
        print("-" * 40)
        return True

    try:
        service_drive = build('drive', 'v3', credentials=creds, cache_discovery=False)
        extractor = ContentExtractor(service_drive, creds)
        bq_loader = BigQueryLoader(BQ_TABLE_ID, creds)

        # 1. Extração
        texto, cnpj, usou_ocr = extractor.process_file(file_id, file_name)

        if texto and "ERRO_OCR" in texto:
            log_buffer.append(f"❌ [ERRO GRAVE] Falha no Poppler/OCR: {texto}")

        # 2. Regras de Negócio
        categoria = classifier.identify_category(file_name)
        periodo = classifier.calculate_period(file_name, categoria)

        # FIX #1: Auditoria da Regra de Data (corrigida)
        # Verifica se o período realmente veio do nome do arquivo
        # O calculate_period retorna MM/YYYY — se esse padrão existe no nome, veio de lá
        import re
        match_data_nome = re.search(r'(0[1-9]|1[0-2])[.\-_](20[2-9][0-9])', file_name)
        origem_data = "NOME ARQUIVO" if match_data_nome else "CALCULADA (M-1/M-2)"

        # 3. Empresa (BUSCA INTELIGENTE: CNPJ + IE + IM)
        # Passamos o texto completo. Ele procura IE, IM e aplica a regra anti-Taxbase.
        empresa_info, cnpj_final = ref_loader.smart_identify_company(texto)

        if empresa_info:
            nome_empresa = empresa_info.get('empresa', 'N/A')
            # Se achamos a empresa pelo IM, atualizamos o CNPJ do registro para o correto da empresa
            cnpj = cnpj_final
            metodo_identificacao = "CNPJ/IE/IM"
        else:
            nome_empresa = 'DESCONHECIDA'
            metodo_identificacao = "NAO_IDENTIFICADO"

        # 4. BigQuery
        registro = {
            "data_processamento": datetime.now().isoformat(),
            "id_arquivo": file_id,
            "nome_arquivo": file_name,
            "link_arquivo": file_meta.get('webViewLink', ''),
            "cnpj": cnpj if cnpj else "NAO_DETECTADO",
            "periodo": periodo,
            "categoria": categoria,
            "status_auditoria": "OCR" if usou_ocr else "TXT",
            "observacao": f"{origem_data} | Empresa: {nome_empresa} ({metodo_identificacao})",
            "pagina": "1"
        }

        sucesso = bq_loader.insert_record(registro)

        # MONTAGEM DO RELATÓRIO FINAL LIMPO
        status = "✅ SUCESSO" if sucesso else "❌ FALHA BQ"
        log_buffer.append(f"{status} | Arq: {file_name}")
        log_buffer.append(f"   ∟ Cat: {categoria} | Período: {periodo} ({origem_data})")
        log_buffer.append(f"   ∟ CNPJ: {cnpj} | Empresa: {nome_empresa}")
        if usou_ocr:
            log_buffer.append(f"   ∟ 👁️ Usou OCR Vision")

        print("\n".join(log_buffer))
        print("-" * 40)
        return True

    except Exception as e:
        print(f"💀 [CRASH] {file_name}: {str(e)}")
        return False


def carregar_ids_existentes(creds):
    """Busca IDs de arquivos já processados no BigQuery para evitar duplicatas."""
    try:
        from google.cloud import bigquery
        client = bigquery.Client(credentials=creds)
        query = f"""
            SELECT DISTINCT id_arquivo 
            FROM `{BQ_TABLE_ID}` 
            WHERE DATE(data_processamento) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        """
        df = client.query(query).to_dataframe()
        ids = set(df['id_arquivo'].tolist()) if not df.empty else set()
        print(f"🛡️ [ANTI-DUPLICATA] {len(ids)} arquivos já processados nos últimos 7 dias.")
        return ids
    except Exception as e:
        print(f"⚠️ [ANTI-DUPLICATA] Falha ao carregar IDs existentes: {e}. Continuando sem proteção.")
        return set()


def main():
    print(f"🚀 [AUDITORIA] Iniciando correção... Poppler deve estar na pasta do projeto.")
    creds = get_credentials()

    watcher = DriveWatcher(creds)
    ref_loader = ReferenceLoader(creds)
    classifier = AuditorClassifier()

    print("📚 Carregando Planilha...")
    ref_loader.load_data()

    print("🛡️ Carregando IDs já processados...")
    ids_existentes = carregar_ids_existentes(creds)

    print("🔎 Buscando arquivos (Isso pode demorar uns segundos)...")
    files_to_process = watcher.get_files_from_yesterday()

    print(f"📋 Fila: {len(files_to_process)} arquivos. Processando em paralelo...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for file_meta in files_to_process:
            future = executor.submit(processar_arquivo_individual, file_meta, creds, ref_loader, classifier, ids_existentes)
            futures.append(future)
        concurrent.futures.wait(futures)

    print("🏁 FIM.")


if __name__ == "__main__":
    main()