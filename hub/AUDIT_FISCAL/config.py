# config.py

# IDs do Google
SPREADSHEET_ID = "19_zhLF-PEPflLtK1LCWsWUDsyUZxB_--VNKjRD2LpOE"
ROOT_FOLDER_ID = "1T7bdlFVEc30gHzvCc42310fsRfMXPPW9"

BQ_TABLE_ID = "auditor-processos.auditoria_fiscal.registros_auditoria"

# Configurações de Colunas (Baseado na sua descrição)
# Índices (Começando do 0: A=0, B=1, ... D=3)
COL_GRUPO = 3      # Coluna D
COL_EMPRESA = 4    # Coluna E
COL_CNPJ = 5       # Coluna F
COL_IE = 11        # Coluna L
COL_IM = 12        # Coluna M

# CNPJ da Taxbase para ignorar se houver outro
CNPJ_TAXBASE = "49756007000127"

# Pastas para ignorar
IGNORE_FOLDERS = ["01 - ENTRADAS", "02 - SAÍDAS"]