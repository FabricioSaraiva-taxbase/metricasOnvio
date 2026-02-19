# Taxbase Platform — Contexto Geral

Repositório monorepo que centraliza todos os sistemas internos da **Taxbase**.

## Arquitetura

```
taxbase-platform/
├── hub/                  ← Portal central (Flask, porta 5000)
├── metricas-onvio/       ← Dashboard de métricas (Next.js + FastAPI, portas 3000/8000)
├── _legacy/              ← Código antigo Streamlit (arquivo morto)
├── service_account.json  ← Credenciais GCP (NÃO committear no Git)
└── start_all.bat         ← Inicia todos os serviços localmente
```

## Módulos

| Módulo | Stack | Porta | Descrição |
|--------|-------|-------|-----------|
| **Hub Taxbase** | Flask + BigQuery | 5000 | Portal de login, gestão de usuários e launcher dos sistemas |
| **Auditor Fiscal** | Streamlit (dentro do Hub) | — | Auditoria de obrigações fiscais |
| **Métricas Onvio** | Next.js + FastAPI + BigQuery | 3000 / 8000 | Dashboard de atendimentos e produtividade |

## Autenticação

- **Hub** gera tokens JWT (HS256) com `SECRET_KEY = taxbase-hub-secret-2026`
- Módulos aceitam o token do Hub via SSO (`/sso?token=JWT`)
- Cada módulo também suporta login local como fallback de desenvolvimento
- Permissões: `admin_master` → `admin` → `usuario` (normalizado para `admin`/`viewer` nos módulos)

## Como Rodar Localmente

1. **Instalar dependências** (uma vez só):
   ```bash
   pip install flask PyJWT google-cloud-bigquery requests
   pip install fastapi uvicorn python-jose pydantic
   cd metricas-onvio/frontend && npm install
   ```

2. **Executar:** duplo-clique em `start_all.bat`

3. **Acessar:** `http://localhost:5000` (Hub)
   - Dev login: `admin@taxbase.com.br` / `admin123`

## Credenciais GCP

- `service_account.json` na raiz é compartilhado entre módulos
- Cada módulo tem seu próprio projeto BigQuery:
  - Hub: `taxbasehub.hub_dados`
  - Métricas: `taxbase-metricasmessenger.metricas`
  - Auditor: `auditor-processos.auditoria_fiscal`

## Documentação por Módulo

- Hub: [`hub/context.md`](hub/context.md)
- Métricas Onvio: [`metricas-onvio/context.md`](metricas-onvio/context.md)

## Guia de Integração

Veja [`INTEGRATION_GUIDE.md`](INTEGRATION_GUIDE.md) para instruções de como adicionar novos módulos.
