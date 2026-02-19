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

## 4. Stack Tecnológica e Arquitetura (Atual - v2.0)
* **Frontend:** Next.js 14 (React, TypeScript, Tailwind CSS, Recharts).
* **Backend:** FastAPI (Python), Pandas, Uvicorn.
* **Database (Produção):** Google BigQuery.
    * *Dataset:* `taxbase-metricasmessenger.metricas`
    * *Padrão de Tabelas:* `atendimentos_YYYY_MM` (ex: `atendimentos_2026_01`).
    * *Tabelas de Configuração:* `config_client_mapping`, `config_departments`, `config_labels`.
* **Mapeamento:** BigQuery (`config_client_mapping`) com fallback para `statusContatos.xlsx` (apenas backup/leitura).
* **Autenticação:** JWT (Local) - Preparado para integração com SSO Taxbase.

## 5. Regras de Ouro (Diretrizes para o Agente)
1.  **Prioridade de Dados:** A "Fonte da Verdade" é o **BigQuery**. O Backend deve sempre tentar ler do BQ primeiro. Arquivos locais (`data/`) são apenas fallback de emergência.
2.  **Performance:** O Backend implementa cache e otimizações de query (ex: Wildcard Tables para períodos grandes). O Frontend usa React Query/SWR ou `useEffect` otimizado para não sobrecarregar a API.
3.  **Deploy e Caminhos:** O projeto roda em ambiente local via `start_app.bat`. Em breve irá para o Hub Taxbase. **Jamais** utilize caminhos absolutos do Windows no código produtivo. Use caminhos relativos ou variáveis de ambiente.
4.  **Manutenção do Código:**
    *   **Backend:** `backend/main.py` (entrypoint), `backend/routers/` (endpoints), `backend/services/` (lógica de negócio).
    *   **Frontend:** `frontend/src/app/` (páginas), `frontend/src/components/` (UI).
    *   Ao criar novas features, mantenha a separação de responsabilidades (Frontend pede dados, Backend processa).

## 6. Estrutura de Arquivos Principal
* `metricas-onvio/backend/`: Código da API FastAPI.
* `metricas-onvio/frontend/`: Código do Next.js.
* `metricas-onvio/service_account.json`: Credenciais do Google (Ignorado no Git).
* `metricas-onvio/requirements.txt`: Dependências do Python (Backend).
* `hub/`: Hub Taxbase (Flask) — portal central.
* `start_all.bat`: Inicia Hub + Backend + Frontend.

## 7. Status do Projeto e Integração (v2.1)
A migração do Streamlit para **Next.js + FastAPI** e a **integração com o Hub Taxbase** foram **CONCLUÍDAS**.

### Integração Hub (Concluída)
*   SSO via JWT: o Hub redireciona para `/sso?token=JWT` com autenticação automática.
*   Botão "← Hub Taxbase" no Navbar para navegação de volta ao portal.
*   Logout inteligente: redireciona ao Hub se veio via SSO, ou ao login local se acesso direto.
*   Backend aceita tokens do Hub (campo `email`/`permissao`) e locais (campo `sub`/`role`).

## 8. Credenciais e Acesso (Desenvolvimento)
*   **Login Local (Metricas direto):** `admin` / `taxbase123` em `http://localhost:3000`
*   **Login via Hub:** `admin@taxbase.com.br` / `admin123` em `http://localhost:5000`
*   **Iniciar tudo:** Execute `start_all.bat` na raiz do repositório.

