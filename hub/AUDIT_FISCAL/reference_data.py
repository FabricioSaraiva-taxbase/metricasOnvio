import re
import pandas as pd
from googleapiclient.discovery import build
from config import SPREADSHEET_ID, CNPJ_TAXBASE


class ReferenceLoader:
    def __init__(self, creds):
        self.service = build('sheets', 'v4', credentials=creds)
        self.df_empresas = None
        self.fast_lookup = {}  # Dicionário de busca rápida
        self.taxbase_clean = self._clean_number(CNPJ_TAXBASE)

    def _clean_number(self, value):
        """Remove tudo que não for dígito."""
        if not value: return ""
        return "".join(filter(str.isdigit, str(value)))

    def _is_red_font(self, cell):
        """Verifica se a célula tem fonte vermelha (empresa inativa)."""
        try:
            fmt = cell.get('effectiveFormat', {})
            fg = fmt.get('textFormat', {}).get('foregroundColor', {})
            r = fg.get('red', 0)
            g = fg.get('green', 0)
            b = fg.get('blue', 0)
            # Vermelho: R > 0.7, G < 0.3, B < 0.3
            return r > 0.7 and g < 0.3 and b < 0.3
        except Exception:
            return False

    def _detect_red_rows(self, sheet):
        """Detecta quais linhas da planilha têm fonte vermelha (empresas inativas).
        Retorna um set com os índices das linhas vermelhas (0-indexed).
        Se falhar, retorna set vazio (fallback seguro)."""
        red_rows = set()
        try:
            result = sheet.get(
                spreadsheetId=SPREADSHEET_ID,
                ranges=["D2:M"],
                includeGridData=True
            ).execute()

            sheets_data = result.get('sheets', [])
            if not sheets_data:
                return red_rows

            grid_data = sheets_data[0].get('data', [])
            if not grid_data:
                return red_rows

            row_data = grid_data[0].get('rowData', [])
            for idx, row_entry in enumerate(row_data):
                cells = row_entry.get('values', [])
                # Verificar as 3 primeiras células (Grupo, Empresa, CNPJ)
                for cell in cells[:3]:
                    if self._is_red_font(cell):
                        red_rows.add(idx)
                        break

            if red_rows:
                print(f"🔴 [SETUP] {len(red_rows)} linhas com fonte vermelha detectadas.")
        except Exception as e:
            print(f"⚠️ [SETUP] Não foi possível verificar formatação de cores: {e}")
            # Fallback: não filtra nada, continua normalmente
        return red_rows

    def load_data(self):
        print("🔍 [SETUP] Carregando e indexando I.E, I.M e CNPJ...")

        sheet = self.service.spreadsheets()

        # PASSO 1: Detectar linhas com fonte vermelha (empresas inativas)
        red_rows = self._detect_red_rows(sheet)

        # PASSO 2: Carregar valores normalmente (método confiável)
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="D2:M").execute()
        rows = result.get('values', [])

        if not rows:
            print("❌ [ERRO] Nenhuma informação encontrada na planilha.")
            return

        data = []
        count_im_ie = 0
        count_skipped_red = 0

        for idx, row in enumerate(rows):
            if len(row) < 3: continue

            # Verificar se esta linha é vermelha (empresa inativa)
            if idx in red_rows:
                count_skipped_red += 1
                continue

            # Garante tamanho 10 para não dar erro de indice
            row_padded = row + [""] * (10 - len(row))

            try:
                grupo = row_padded[0]  # Coluna D
                empresa = row_padded[1]  # Coluna E
                cnpj = self._clean_number(row_padded[2])  # Coluna F
                ie = self._clean_number(row_padded[8])  # Coluna L (I.E)
                im = self._clean_number(row_padded[9])  # Coluna M (I.M)

                if cnpj:
                    record = {
                        "grupo": grupo,
                        "empresa": empresa,
                        "cnpj": cnpj,
                        "ie": ie,
                        "im": im
                    }
                    data.append(record)

                    # --- INDEXAÇÃO PODEROSA ---
                    # Adiciona no dicionário de busca rápida por todos os campos
                    if cnpj: self.fast_lookup[cnpj] = record
                    if ie:
                        self.fast_lookup[ie] = record
                        count_im_ie += 1
                    if im:
                        self.fast_lookup[im] = record
                        count_im_ie += 1

            except Exception as e:
                continue

        self.df_empresas = pd.DataFrame(data)
        print(f"✅ [SETUP] Base indexada! {len(self.df_empresas)} empresas ativas. {count_im_ie} I.E/I.M mapeados para busca.")
        if count_skipped_red > 0:
            print(f"🔴 [SETUP] {count_skipped_red} empresas inativas (fonte vermelha) foram ignoradas.")

    def smart_identify_company(self, text):
        """
        Recebe o TEXTO COMPLETO do PDF e procura qualquer vestígio da empresa
        (CNPJ, IE ou IM). Aplica a regra de exclusão da Taxbase.
        """
        if not text: return None, None

        # 1. Limpa o texto do PDF para deixar apenas sequências numéricas
        # Remove pontos, traços e barras para bater com o banco de dados
        text_clean = text.replace('.', '').replace('-', '').replace('/', '')

        # Encontra todas as sequências numéricas de 5 dígitos ou mais (para ignorar lixo)
        # Ex: Pega 12345678000199 (CNPJ), pega 123456 (IM)
        found_tokens = re.findall(r'\d{5,}', text_clean)

        matches = []
        seen_cnpjs = set()

        # 2. Verifica cada número achado no PDF contra nosso banco de dados
        for token in found_tokens:
            if token in self.fast_lookup:
                empresa_match = self.fast_lookup[token]
                cnpj_match = empresa_match['cnpj']

                # Evita duplicatas na lista de candidatos
                if cnpj_match not in seen_cnpjs:
                    matches.append(empresa_match)
                    seen_cnpjs.add(cnpj_match)

        if not matches:
            return None, None

        # 3. REGRA DE OURO: Filtragem da Taxbase
        # Se houver qualquer empresa que NÃO seja a Taxbase, usamos ela.
        non_taxbase = [m for m in matches if m['cnpj'] != self.taxbase_clean]

        if non_taxbase:
            # SUCESSO: Achamos um cliente (pelo CNPJ, IE ou IM)
            # Retorna o CNPJ correto do cliente (mesmo que o PDF só tivesse o IM)
            best_match = non_taxbase[0]
            return best_match, best_match['cnpj']

        # Se só sobrou a Taxbase na lista, paciência, é um documento da Taxbase mesmo
        if matches:
            return matches[0], matches[0]['cnpj']

        return None, None

    # Mantemos esse para compatibilidade se precisar buscar só por CNPJ direto
    def find_company(self, search_term):
        clean = self._clean_number(search_term)
        if clean in self.fast_lookup:
            return self.fast_lookup[clean]
        return None