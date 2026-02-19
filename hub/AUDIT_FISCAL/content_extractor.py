import io
import os
import re
from googleapiclient.http import MediaIoBaseDownload
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from google.cloud import vision
from pdf2image import convert_from_bytes
from config import CNPJ_TAXBASE


# --- FUNÇÃO DE RASTREAMENTO INTELIGENTE DO POPPLER ---
def find_poppler_bin():
    """
    Varre a pasta do projeto procurando onde está o executável 'pdftoppm.exe'.
    Isso garante que funcione para poppler-25.12.0, 24.04, ou qualquer outro nome.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Procura em profundidade dentro da pasta do projeto
    for root, dirs, files in os.walk(project_root):
        if "pdftoppm.exe" in files:
            return root  # Retorna a pasta exata onde achou o executável

    return None


# Executa a busca uma vez ao carregar o script
DETECTED_POPPLER_PATH = find_poppler_bin()


class ContentExtractor:
    def __init__(self, drive_service, creds):
        self.drive_service = drive_service
        self.creds = creds  # <--- ARMAZENA AS CREDENCIAIS PARA O VISION
        self.vision_client = None
        # Regex captura: XX.XXX.XXX/XXXX-XX ou apenas números (14 dígitos)
        self.cnpj_pattern = re.compile(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}')

    def process_file(self, file_id, file_name):
        """
        Fluxo Principal:
        1. Baixa o PDF.
        2. Tenta ler texto direto (rápido).
        3. Se falhar ou for Taxbase -> Usa OCR com Poppler + Vision.
        Retorna: (texto_final, cnpj_encontrado, bool_usou_ocr)
        """
        pdf_bytes = self._download_file(file_id)

        if not pdf_bytes:
            return None, None, False

        # --- TENTATIVA 1: Extração via Software (PDFMiner) ---
        text_soft = self._pdf_to_txt_layout(pdf_bytes)
        cnpj = self._extract_best_cnpj(text_soft)

        # --- VALIDAÇÃO: Precisa de OCR? ---
        # Regra: Se CNPJ é None OU se o CNPJ encontrado for o da Taxbase (que ignoramos)
        needs_ocr = (cnpj is None) or (cnpj == self._clean_cnpj(CNPJ_TAXBASE))

        if needs_ocr:
            # Verifica se o Poppler foi encontrado antes de tentar usar
            # MODIFICADO: No Cloud Run (Linux), esperamos que o poppler esteja no PATH (instalado via apt-get).
            # Então se DETECTED_POPPLER_PATH for None, permitimos tentar sem path explícito.
            # if not DETECTED_POPPLER_PATH:
            #    return "ERRO_POPPLER_FATAL: ...", cnpj, False
            pass

            # --- TENTATIVA 2: OCR (PDF -> Imagem -> Vision) ---
            try:
                # Converte a 1ª página do PDF em Imagem (JPG)
                images = convert_from_bytes(
                    pdf_bytes,
                    first_page=1,
                    last_page=1,
                    poppler_path=DETECTED_POPPLER_PATH
                )

                if images:
                    img_byte_arr = io.BytesIO()
                    images[0].save(img_byte_arr, format='JPEG')
                    image_content = img_byte_arr.getvalue()

                    # Manda para o Google Vision
                    text_ocr = self._perform_ocr_on_image(image_content)

                    # Tenta achar CNPJ no texto do OCR
                    cnpj_ocr = self._extract_best_cnpj(text_ocr)

                    if cnpj_ocr:
                        return text_ocr, cnpj_ocr, True
                    else:
                        return text_ocr, cnpj, True

            except Exception as e:
                error_msg = str(e)
                if "Unable to get page count" in error_msg:
                    return f"ERRO_POPPLER: Falha ao executar binário em {DETECTED_POPPLER_PATH}.", cnpj, False

                return f"ERRO_OCR_GERAL: {error_msg}", cnpj, False

        return text_soft, cnpj, False

    def _download_file(self, file_id):
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            return fh.getvalue()
        except Exception:
            return None

    def _pdf_to_txt_layout(self, pdf_bytes):
        try:
            laparams = LAParams()
            text = extract_text(io.BytesIO(pdf_bytes), laparams=laparams)
            return text if text else ""
        except Exception:
            return ""

    def _clean_cnpj(self, cnpj):
        if not cnpj: return ""
        return "".join(filter(str.isdigit, cnpj))

    def _extract_best_cnpj(self, text):
        if not text: return None

        found = self.cnpj_pattern.findall(text)
        unique_cnpjs = set(self._clean_cnpj(c) for c in found)

        target_taxbase = self._clean_cnpj(CNPJ_TAXBASE)

        # Regra: Se tiver Taxbase + Outro, remove Taxbase e fica com o Outro
        if len(unique_cnpjs) > 1 and target_taxbase in unique_cnpjs:
            unique_cnpjs.remove(target_taxbase)

        if unique_cnpjs:
            return list(unique_cnpjs)[0]

        return None

    def _perform_ocr_on_image(self, image_bytes):
        # CORREÇÃO: Passa as credenciais explicitamente para o cliente
        if not self.vision_client:
            self.vision_client = vision.ImageAnnotatorClient(credentials=self.creds)

        try:
            image = vision.Image(content=image_bytes)
            response = self.vision_client.document_text_detection(image=image)

            if response.error.message:
                return f"ERRO API VISION: {response.error.message}"

            return response.full_text_annotation.text
        except Exception as e:
            # Retorna o erro para aparecer no log de diagnóstico
            raise e