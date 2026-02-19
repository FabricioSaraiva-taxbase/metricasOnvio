from googleapiclient.discovery import build
from google.oauth2 import service_account
from config import ROOT_FOLDER_ID

KEY_FILE = 'credentials.json'


def debug_permissions():
    print(f"🕵️ INICIANDO DIAGNÓSTICO (MODO SHARED DRIVE)...")
    print(f"📂 ID da Pasta Configurada: {ROOT_FOLDER_ID}")

    creds = service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=creds)

    # TESTE 1: O robô consegue ver a pasta raiz?
    try:
        # MUDANÇA: supportsAllDrives=True é OBRIGATÓRIO para pastas de Organização
        folder = service.files().get(
            fileId=ROOT_FOLDER_ID,
            fields="id, name",
            supportsAllDrives=True
        ).execute()
        print(f"✅ [SUCESSO] Pasta Raiz encontrada: '{folder.get('name')}'")
    except Exception as e:
        print(f"❌ [ERRO] Falha ao acessar. Verifique se o e-mail do robô está na pasta.")
        print(f"   Detalhe: {e}")
        return

    # TESTE 2: Listagem (também precisa dos parâmetros extras)
    print("\n📄 Listando arquivos DENTRO desta pasta:")
    results = service.files().list(
        q=f"'{ROOT_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name, mimeType)",
        pageSize=10,
        # Parâmetros vitais para Drives de Organização:
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    files = results.get('files', [])

    if not files:
        print("⚠️ [ALERTA] A pasta está acessível, mas parece vazia.")
    else:
        print(f"✅ [SUCESSO] O robô enxerga {len(files)} itens (Exemplos):")
        for f in files:
            print(f"   - {f['name']}")


if __name__ == "__main__":
    debug_permissions()