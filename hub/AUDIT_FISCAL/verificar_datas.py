from googleapiclient.discovery import build
from google.oauth2 import service_account
from config import ROOT_FOLDER_ID

KEY_FILE = 'credentials.json'


def check_dates():
    creds = service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=['https://www.googleapis.com/auth/drive']
    )
    service = build('drive', 'v3', credentials=creds)

    print(f"🕵️ Investigando datas reais na pasta: {ROOT_FOLDER_ID}")

    # Lista arquivos sem filtro de data, para ver a verdade nua e crua
    results = service.files().list(
        q=f"'{ROOT_FOLDER_ID}' in parents and trashed=false",
        fields="files(id, name, createdTime, mimeType)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    files = results.get('files', [])
    print(f"📂 Encontrados {len(files)} arquivos:")

    for f in files:
        print(f"   📄 {f['name']}")
        print(f"      🕒 Data Google (UTC): {f['createdTime']}")
        print(f"      📎 Tipo: {f['mimeType']}")
        print("-" * 30)


if __name__ == "__main__":
    check_dates()