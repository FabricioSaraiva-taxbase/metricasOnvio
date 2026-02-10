# PROJETO: Metricas ONVIO (Taxbase) - Contexto de Negócio e Técnico

## 1. Visão Geral e Propósito
Este projeto é um Dashboard de BI desenvolvido para a equipe de TI da Taxbase.
**O Problema:** A plataforma de chat (Onvio/Messenger) exporta logs de atendimento contendo o nome da pessoa que entrou em contato (ex: "Maria Silva"), mas só informa a qual empresa (Cliente) ela pertence SE for feito um alocamento manual na plataforma Portal do Cliente, do sistema Onvio, mas isso depende de que o contato tenha uma conta registrada e com email confirmado no Portal do Cliente, o que nem sempre acontece. Isso impede a análise de lucratividade e demanda por cliente.
**A Solução:** Um sistema que cruza os logs de chat com uma base de conhecimento que eu criei (`statusContatos.xlsx`) para realizar um "De/Para" automático, permitindo visualizar métricas reais de atendimento por empresa.

## 2. Dicionário de Entidades (Conceitos Chave)
Para garantir a lógica correta, diferencie:
* **CONTATO (Raw Data):** É a pessoa física que manda mensagem no chat. O nome vem muitas vezes incompleto ou informal (ex: "Junior Financeiro", "Ana - Padaria").
    * *Origem:* BigQuery (Tabela `atendimentos_YYYY_MM`) ou CSVs brutos.
* **CLIENTE (Entidade Final):** É a empresa contratante (PJ) para a qual prestamos serviço. É a métrica que importa para o faturamento (ex: "PADARIA PÃO QUENTE LTDA").
    * *Origem:* Coluna `Cliente_Alvo` no arquivo `statusContatos.xlsx`.
* **VÍNCULO:** A relação é de **N:1** (Muitos Contatos pertencem a um Cliente).

## 3. Lógica de Negócio Central: O "De/Para"
O coração do sistema é a função de higienização e merge. O agente deve sempre respeitar este fluxo:

1.  **Ingestão:** Ler os dados brutos de atendimento (preferencialmente do BigQuery).
2.  **Normalização:** Converter a coluna `Contato` para maiúsculo e remover espaços extras (`strip().upper()`).
3.  **Cruzamento (Mapping):**
    * Ler o arquivo `statusContatos.xlsx`.
    * Comparar `Contato` (Log) com `NOME DO CONTATO` (Excel).
    * Se houver *match*: Preencher a coluna `Cliente_Final` com o `NOME CLIENTE` correspondente.
    * Se **não** houver *match*: Preencher `Cliente_Final` como **"NÃO IDENTIFICADO"**.
4.  **Feedback Loop:** O dashboard possui uma interface para o usuário cadastrar manualmente os "NÃO IDENTIFICADO". Quando isso ocorre, o sistema deve atualizar o `statusContatos.xlsx` e recarregar os dados.

## 4. Stack Tecnológica e Arquitetura
* **Frontend:** Streamlit (Python).
* **Database (Produção):** Google BigQuery.
    * *Dataset:* `taxbase-metricasmessenger.metricas`
    * *Padrão de Tabelas:* `atendimentos_YYYY_MM` (ex: `atendimentos_2026_01`).
* **Database (Legado/Backup):** Arquivos CSV locais na pasta `data/` e `dataBackup/`. (Devem ser usados apenas se o BigQuery falhar ou não estiver configurado).
* **Mapeamento:** `statusContatos.xlsx` (Arquivo local Excel que atua como banco de dados relacional simples).
* **Visualização:** Plotly Express (Gráficos de barras e linhas).

## 5. Regras de Ouro (Diretrizes para o Agente)
1.  **Prioridade de Dados:** A "Fonte da Verdade" é o **BigQuery**. Se a variável `HAS_BQ` for verdadeira, ignore os arquivos CSV locais para evitar duplicidade de dados.
2.  **Performance:** Utilize `@st.cache_data` para funções de leitura de dados (`carregar_dados_mes` e `listar_arquivos`). O cache deve ter TTL (tempo de vida) para não mostrar dados obsoletos.
3.  **Deploy e Caminhos:** O projeto roda atualmente em ambiente local e Streamlit Cloud. Em breve irá para Google Cloud Run. **Jamais** utilize caminhos absolutos do Windows (ex: `C:\Users\...`). Use caminhos relativos (ex: `data/arquivo.csv`).
4.  **Manutenção do Código:**
    * O arquivo principal é `app_metricas.py`. Evite quebrar o código em múltiplos arquivos pequenos sem necessidade.
    * Ao sugerir alterações, foque na robustez da função de tratamento de datas (diferença entre formatos `YYYY-MM-DD` do Google vs `DD/MM/YYYY` local).

## 6. Estrutura de Arquivos
* `app_metricas.py`: Código fonte principal.
* `statusContatos.xlsx`: Base de conhecimento para o De/Para.
* `service_account.json`: Credenciais do Google (Ignorado no Git).
* `.gitignore`: Define o que não deve ser versionado/lido.

OBS: O login padrão é 'admin' e senha 'taxbase123'