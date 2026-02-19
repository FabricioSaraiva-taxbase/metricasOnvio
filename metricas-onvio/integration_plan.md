# Plano de Integração: Metricas ONVIO → Taxbase Hub

## 1. Análise de Arquitetura

### Situação Atual (Taxbase Hub)
*   **Tipo:** Monolito (Python/Flask + Jinja2 Templates).
*   **Frontend:** HTML/CSS/JS (Vanilla) servido pelo Flask.
*   **Database:** BigQuery.
*   **Auth:** JWT Próprio (`PyJWT`), armazenado em `localStorage` e validado no Backend.
*   **Módulos:** "Auditor Fiscal" é um sub-módulo Python (`AUDIT_FISCAL/`) importado diretamente no `app.py`.

### Situação Atual (Metricas ONVIO)
*   **Tipo:** Arquitetura Decoplada (Frontend + Backend).
*   **Frontend:** Next.js 14 (React, Tailwind) - Servidor Node.js.
*   **Backend:** FastAPI (Python) - Servidor Python (Uvicorn).
*   **Database:** BigQuery.
*   **Auth:** JWT Local (Similares ao Hub, mas isolado).

## 2. Estratégia de Integração: "Sidecar" (Micro-Frontend)

Dado que o "Metricas ONVIO" possui um Frontend moderno (Next.js) que oferece UX superior ao Jinja2, **NÃO** recomendamos reescrevê-lo dentro do Flask.
A estratégia será rodar o Metricas "ao lado" do Hub, integrando apenas a Autenticação e a Navegação.

### Fluxo Proposto
1.  **Usuário Loga no Hub:** Recebe token JWT do Hub.
2.  **Clica no ícone "Métricas Onvio":** O Hub redireciona para a URL do Next.js (ex: `metrics.hub.taxbase.local`), passando o token.
3.  **Metricas Valida Token:** O Backend do Metricas (FastAPI) passa a aceitar o JWT do Hub (mesma `SECRET_KEY`).
4.  **Experiência Unificada:** O Next.js exibe uma "Navbar Simplificada" ou botão "Voltar ao Hub" para manter a coesão.

## 3. Plano de Implementação (Passo a Passo)

### Fase 1: Unificação de Segredos e Auth
*   [ ] **Configurar Secret:** Copiar a `SECRET_KEY` do Hub para o `.env` do Metricas.
*   [ ] **Ajustar FastAPI (`backend/core/auth.py`):**
    *   Alterar a validação de token para decodificar o formato de payload do Hub (`funcao_id`, `permissao`, etc).
    *   Remover login local do Metricas (ou mantê-lo apenas como fallback de dev).

### Fase 2: Configuração do Hub
*   [ ] **Registrar Sistema:** Adicionar uma entrada em `sistemas_taxbase.json` (e no BigQuery `sistemas`) apontando para a URL do Metricas.
    ```json
    {
        "nome": "Métricas Onvio",
        "sistema_id": "METRICAS_ONVIO",
        "url": "http://localhost:3000", // Dev
        "categoria": "Operacional",
        "desc": "Dashboard de atendimentos e produtividade",
        "status_manual": "Automático"
    }
    ```

### Fase 3: Deployment Unificado (Docker & Cloud Run)

Aqui é onde a mágica acontece para sair do `localhost`.

#### Estratégia de Deploy (Microserviços)
No Google Cloud Run, não "hospedamos" tudo no mesmo container. Criaremos serviços separados que conversam entre si.

1.  **Serviço Hub (Já existe):** `https://hubtaxbase-xyz.run.app`
2.  **Serviço Metricas Backend (Novo):** `https://metricas-api-xyz.run.app` (FastAPI)
3.  **Serviço Metricas Frontend (Novo):** `https://metricas-web-xyz.run.app` (Next.js)

#### Como eles se conectam? (Variáveis de Ambiente)
Não usaremos `localhost`. Usaremos variáveis que serão injetadas ou no `docker-compose` (local) ou no Cloud Run (produção).

*   **No Next.js (Frontend):**
    *   `NEXT_PUBLIC_API_URL`: Aponta para a URL do Backend (ex: `https://metricas-api-xyz.run.app`).
    *   `NEXT_PUBLIC_HUB_URL`: Aponta para a URL do Hub (ex: `https://hubtaxbase-xyz.run.app`).
*   **No Hub:**
    *   Atualizar a tabela `sistemas` para apontar para `https://metricas-web-xyz.run.app` em vez de `localhost:3000`.

#### Arquivos Necessários
*   [ ] **Dockerfile.backend:** Para containerizar o FastAPI.
*   [ ] **Dockerfile.frontend:** Para containerizar o Next.js.
*   [ ] **docker-compose.yml:** Para testar essa orquestração localmente antes de subir.

### Fase 4: Ajustes de UX (Frontend Next.js)
*   [ ] **Navbar:** Adicionar link "Voltar ao Hub".
*   [ ] **Auth Guard:** Se o usuário tentar acessar sem token (direto no link), redirecionar para o Login do Hub (`localhost:5000`).

## 4. Benefícios desta Abordagem
*   **Preserva o Investimento:** Mantém todo o código Next.js moderno e responsivo.
*   **Baixo Acoplamento:** Se o Hub mudar, o Metricas continua funcionando (apenas a interface de Auth conecta os dois).
*   **Escalabilidade:** Permite que futuros módulos também sejam feitos em stacks modernas (React/Vue) sem ficar preso ao Flask/Jinja2.

3. Autorizar a modificação do `backend/core/auth.py` do Metricas para aceitar tokens do Hub.

## 6. Contexto Técnico para o Próximo Agente (Handover)

**ATENÇÃO AGENTE:** Use esta seção para pular a etapa de "Exploração Profunda". Aqui está tudo o que você precisa saber sobre o ambiente do Hub.

### A. Autenticação (Crucial)
O Hub usa JWT (`PyJWT`) com algoritmo **HS256**.
*   **Segredo:** Definido via env `SECRET_KEY`. No Hub (local) padrão é `'taxbase-hub-secret-2026'`.
*   **Payload do Token (Hub):**
    ```json
    {
        "email": "usuario@taxbase.com.br",
        "nome": "Nome Usuario",
        "funcao_id": "analista_fiscal",
        "permissao": "usuario", // ou 'admin', 'admin_master'
        "sistemas": ["METRICAS_ONVIO", "AUDIT_FISCAL"],
        "exp": 1739800000
    }
    ```
*   **Local do Código Auth no Hub:** `HUB_TAXBASE/app.py` (função `gerar_token` e `auth_required`).

### B. Estrutura de Pastas e Arquivos Chave
*   **Hub (Monolito):** `c:\Users\User\Desktop\Metricas ONVIO - Versao Antigravity\HUB_TAXBASE\`
    *   `app.py`: Backend Flask (Rotas API + Auth).
    *   `templates/`: HTML Jinja2 (Interface).
    *   `static/`: CSS/JS.
    *   `sistemas_taxbase.json`: Configuração dos ícones na home do Hub.
*   **Metricas (Nosso Projeto):** `c:\Users\User\Desktop\Metricas ONVIO - Versao Antigravity\`
    *   `backend/core/auth.py`: Onde você deve implementar a validação do token do Hub.
    *   `frontend/src/middleware.ts`: (Se existir) Onde proteger rotas no Next.js.

### C. Tabelas BigQuery (Hub)
*   **Dataset:** `taxbasehub.hub_dados`
*   **Usuários:** `hub_dados.usuarios` (Colunas: `email`, `nome`, `senha` (hash), `funcao_id`).
*   **Sistemas:** `hub_dados.sistemas` (Colunas: `sistema_id`, `url`, `nome`, `categoria`).
    *   *Ação Necessária:* Inserir o sistema "METRICAS_ONVIO" aqui.

### D. Diretrizes de Execução (Economia de Tokens)
1.  **Não analise** todo o código do Hub. Foque apenas em `app.py` para confirmar a `SECRET_KEY` e a estrutura do JWT.
2.  **Não tente migrar** o Next.js para dentro do Flask. Mantenha-os rodando em paralelo (`docker-compose` ou scripts de start separados).
3.  **Foco na Integração:** Sua única tarefa real de código é fazer o Backend do Metricas aceitar o Token do Hub e configurar o redirecionamento.

