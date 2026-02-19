import re
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AuditorClassifier:
    def __init__(self):
        # ========================================================
        # BLACKLIST: Nomes de arquivo que devem ser IGNORADOS
        # Se qualquer termo abaixo aparecer no nome do arquivo,
        # ele será pulado antes de qualquer processamento.
        # ========================================================
        self.BLACKLIST = [
            # --- Notas Fiscais (Entrada/Saída) ---
            "NOTA FISCAL", "NF-E", "NFE", "NFS-E", "NFSE", "DANFE",
            "NOTA DE ENTRADA", "NOTA DE SAIDA", "NOTA DE SAÍDA",
            "NF ENTRADA", "NF SAIDA", "NF SAÍDA",
            "NOTA SERVICO", "NOTA SERVIÇO",
            # --- Boletos e Pagamentos ---
            "BOLETO", "FATURA", "DUPLICATA", "COBRANCA", "COBRANÇA",
            # --- Comprovantes genéricos ---
            "COMPROVANTE DE PAGAMENTO", "COMPROVANTE PAGTO",
            "COMPROVANTE DE ENDERECO", "COMPROVANTE DE ENDEREÇO",
            # --- Contratos e Documentos ---
            "CONTRATO", "PROCURACAO", "PROCURAÇÃO", "ALVARA", "ALVARÁ",
            # --- Extratos e Financeiros ---
            "EXTRATO BANCARIO", "EXTRATO BANCÁRIO",
            # --- Certidões ---
            "CERTIDAO", "CERTIDÃO", "CND ",
            # --- Contabilidade ---
            "BALANCETE", "BALANCO", "BALANÇO", "DRE ",
            # --- RH / Departamento Pessoal ---
            "FOLHA DE PAGAMENTO", "HOLERITE", "CONTRA CHEQUE", "CONTRACHEQUE",
            "RESCISAO", "RESCISÃO", "FERIAS", "FÉRIAS",
            # --- Outros irrelevantes ---
            "RECIBO DE ALUGUEL",
            "XML ",
            "NFS ",
            "TERMO DE INDEFERIMENTO", "INDEFERIMENTO",
            "MEMORIA DE CALCULO", "MEMÓRIA DE CÁLCULO",
            "RESUMO DE ENTRADAS", "RESUMO DE SAIDAS", "RESUMO DE SAÍDAS",
        ]

        # ========================================================
        # CATEGORIES: Palavras-chave para classificação fiscal
        # Ordem importa! Categorias com termos mais específicos
        # devem vir antes das mais genéricas.
        # ========================================================
        self.CATEGORIES = {
            "ISS": ["ISS PRESTADO", "ISS PRESTADOS", "ISS TOMADO", "ISS TOMADOS",
                     "GUIA ISS", "ISS RETIDO", "ISS"],
            "EFD_CONTRIBUICOES": ["EFD CONTRIBUIÇÕES", "EFD CONTRIBUICOES", "EFD CONTRI",
                                  "EFD CONTR", "EFD CONTRIB",
                                  "SPED CONTRIBUICOES", "SPED CONTRIBUIÇÕES",
                                  "SPED CONTR", "SPED CONTRIB",
                                  "PIS COFINS EFD",
                                  "RECIBO CONTRI", "RECIBO CONTRIBUIÇÕES", "RECIBO CONTRIBUICOES"],
            "REINF": ["EFD REINF", "REINF"],
            "IRRF": ["IRRF", "EFD IRRF", "DARF IRRF"],
            "GUIA_ICMS": ["GUIA ICMS", "GARE ICMS", "DARE ICMS", "GARE-ICMS", "DARE-ICMS", "ICMS"],
            "SIMPLES_NACIONAL": ["SIMPLES NACIONAL", "DAS SIMPLES", "PGDAS-D", "PGDAS",
                                 "DEFIS", "DAS ", "SIMPLES"],
            "SPED_ICMS": ["SPED ICMS", "EFD ICMS IPI", "EFD ICMS", "SPED FISCAL",
                          "RECIBO ICMS", "RECIBO SPED", "SPED"],
            "GIA_ICMS": ["GIA ICMS", "GIA ST", "GIA SP", "NOVA GIA", "GIA"],
            "DIRB": ["DIRB"],
            "IPI": ["APURACAO IPI", "APURAÇÃO IPI", "IPI"],
            "PIS_COFINS": ["PIS COFINS", "PIS E COFINS", "PIS-COFINS", "PIS - COFINS",
                           "DARF PIS", "DARF COFINS", "PIS", "COFINS"],
            "PARCELAMENTO": ["PARCELAMENTO", "REPARCELAMENTO", "PARCSN", "REFIS",
                             "PARCELA", "PARC.", "PARC "],
            "ICMS_ST": ["ICMS ST", "SUBSTITUICAO TRIBUTARIA", "SUBSTITUIÇÃO TRIBUTÁRIA"],
            "ICMS_DIFAL": ["ICMS DIFAL", "DIFERENCIAL DE ALIQUOTA", "DIFERENCIAL DE ALÍQUOTA"],
            "IRPJ_CSLL": ["IRPJ E CSLL", "IRPJ_CSLL", "DARF IRPJ", "DARF CSLL",
                          "IRPJ", "CSLL", "ECF ", "LALUR"],
            "MIT": ["MIT"],
            "DCTFWEB": ["DCTFWEB", "DCTF WEB", "DCTF-WEB", "DCTFW", "DCTF"],
            "DSTDA": ["DSTDA", "DS-TDA", "DESTDA"],
        }

    def is_blacklisted(self, filename):
        """
        Retorna True se o arquivo deve ser IGNORADO (não processado).
        Verifica se o nome do arquivo contém algum termo da blacklist.
        """
        name_upper = filename.upper().rsplit('.', 1)[0]
        for term in self.BLACKLIST:
            if term in name_upper:
                return True
        return False

    def identify_category(self, filename):
        """Identifica a categoria baseada no nome do arquivo."""
        filename_upper = filename.upper()
        # Remove extensão para evitar falsos positivos
        name_body = filename_upper.rsplit('.', 1)[0]

        for category, keywords in self.CATEGORIES.items():
            for keyword in keywords:
                if keyword in name_body:
                    return category
        return "NAO_IDENTIFICADO"

    def calculate_period(self, filename, category, processing_date=None):
        """
        Define o período da obrigação.
        Prioridade 1: Data no nome do arquivo (ex: 01.2026).
        Prioridade 2: Data de processamento - X meses (Regra de Negócio).
        """
        # 1. Tenta extrair do nome do arquivo
        match = re.search(r'(0[1-9]|1[0-2])[.\-_](20[2-9][0-9])', filename)
        if match:
            return f"{match.group(1)}/{match.group(2)}"

        # 2. Se não achar, usa a regra baseada na data atual
        if processing_date is None:
            processing_date = datetime.now()

        months_back = 1  # Regra Padrão

        if category == "EFD_CONTRIBUICOES":
            months_back = 2  # Regra de Exceção

        target_date = processing_date - relativedelta(months=months_back)
        return target_date.strftime("%m/%Y")


# Exemplo de uso (Teste Rápido):
# auditor = AuditorClassifier()
# cat = auditor.identify_category("Recibo EFD Contribuicoes.pdf")
# per = auditor.calculate_period("Recibo EFD Contribuicoes.pdf", cat)
# print(f"Categoria: {cat} | Período: {per}")
# Saída esperada (se hoje fosse Fev/2026): Categoria: EFD_CONTRIBUICOES | Período: 12/2025