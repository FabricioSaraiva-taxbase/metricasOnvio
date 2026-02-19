from datetime import datetime, timedelta
from googleapiclient.discovery import build
from config import ROOT_FOLDER_ID, IGNORE_FOLDERS


class DriveWatcher:
    def __init__(self, creds):
        self.service = build('drive', 'v3', credentials=creds)
        # Cache para não ficar batendo na API toda hora
        # True = Pasta Segura | False = Pasta Proibida
        self.folder_cache = {ROOT_FOLDER_ID: True}

    def get_files_from_yesterday(self):
        print("📅 [DRIVE] Iniciando varredura com FILTRO DE PASTAS ATIVO...")

        # MANTENHA O PERÍODO QUE VOCÊ QUER (5 dias para teste, 1 para produção)
        today = datetime.now().date()
        start_date = today - timedelta(days=1)
        query_date = start_date.isoformat()

        # Normaliza a lista de pastas proibidas para maiúsculo para comparar sem erro
        self.ignore_list_upper = [f.upper() for f in IGNORE_FOLDERS]

        print(f"🚫 Lista Negra de Pastas: {self.ignore_list_upper}")
        print(f"🔎 Buscando arquivos (Global) > {query_date}...")

        # 1. Busca Global (Rápida)
        files_found = []
        page_token = None

        while True:
            # Pega TODOS os PDFs recentes (A filtragem de pasta acontece ABAIXO)
            response = self.service.files().list(
                q=f"trashed=false and createdTime > '{query_date}T00:00:00' and mimeType='application/pdf'",
                spaces='drive',
                corpora='allDrives',
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="nextPageToken, files(id, name, parents, webViewLink)",
                pageToken=page_token
            ).execute()

            items = response.get('files', [])

            for file in items:
                name = file.get('name')
                parents = file.get('parents', [])

                if not parents: continue

                parent_id = parents[0]

                # --- AQUI É A BARREIRA DE SEGURANÇA ---
                # Só adiciona na lista se passar na validação de pasta
                is_valid, motivo = self._check_folder_safety(parent_id)

                if is_valid:
                    files_found.append(file)
                else:
                    print(f"⛔ [BLOQUEADO] {name} | Motivo: {motivo}")

            page_token = response.get('nextPageToken')
            if not page_token:
                break

        # 2. Fallback (Busca Local na Raiz) se a Global falhar totalmente
        if not files_found:
            print("⚠️ Busca Global vazia. Tentando Busca Local na pasta raiz...")
            try:
                response = self.service.files().list(
                    q=f"'{ROOT_FOLDER_ID}' in parents and trashed=false and createdTime > '{query_date}T00:00:00' and mimeType='application/pdf'",
                    spaces='drive',
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True,
                    fields="files(id, name, parents, webViewLink)",
                ).execute()
                files_found = response.get('files', [])
                if files_found:
                    print(f"✅ Busca Local encontrou {len(files_found)} arquivos na raiz.")
                else:
                    print("📭 Nenhum arquivo encontrado nem na busca local.")
            except Exception as e:
                print(f"❌ Falha na busca local: {e}")

        return files_found

    def _check_folder_safety(self, folder_id):
        """
        Verifica se a pasta é segura. Retorna (True/False, "Motivo")
        """
        # 1. Checa Cache
        if folder_id in self.folder_cache:
            if self.folder_cache[folder_id]:
                return True, "Cache OK"
            else:
                return False, "Cache Bloqueado"

        try:
            folder = self.service.files().get(
                fileId=folder_id,
                fields="id, name, parents",
                supportsAllDrives=True
            ).execute()
        except Exception as e:
            # FIX #2: Captura exceção específica em vez de bare except
            print(f"⚠️ [PASTA] Erro ao acessar pasta {folder_id}: {e}")
            self.folder_cache[folder_id] = False
            return False, f"Erro de Permissão na Pasta: {e}"

        folder_name = folder.get('name', '').upper()

        # 2. REGRA DE OURO: Verifica se o nome contém termo proibido
        for forbidden in self.ignore_list_upper:
            if forbidden in folder_name:
                self.folder_cache[folder_id] = False
                return False, f"Pasta Proibida Detectada: {folder_name}"

        # 3. Verifica se é a Raiz do Projeto
        if folder_id == ROOT_FOLDER_ID:
            self.folder_cache[folder_id] = True
            return True, "Raiz do Projeto"

        # 4. Verifica Pais (Recursão para cima)
        parents = folder.get('parents', [])
        if not parents:
            self.folder_cache[folder_id] = False
            return False, "Chegou no topo do Drive e não achou a Raiz Configurada"

        # Sobe um nível
        parent_valid, parent_reason = self._check_folder_safety(parents[0])

        # Salva o resultado deste nível no cache
        self.folder_cache[folder_id] = parent_valid
        return parent_valid, parent_reason