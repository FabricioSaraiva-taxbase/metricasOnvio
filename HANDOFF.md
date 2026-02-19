# Handoff: Taxbase Platform (v2.1)

👋 **Olá! Bem-vindo ao novo monorepo `taxbase-platform`.**

Se você é o próximo agente ou desenvolvedor assumindo este projeto, aqui está o estado atual das coisas.

## 🔄 O Que Acabou de Acontecer
O projeto migrou de uma estrutura "flat" (tudo na raiz) para um **monorepo organizado**:
- **`hub/`**: O sistema central (Flask).
- **`metricas-onvio/`**: O módulo de dashboard (FastAPI + Next.js).
- **`_legacy/`**: Arquivos antigos do Streamlit (apenas referência).

## 🚀 Status Atual
- **Integração Concluída**: O Hub e o Métricas conversam via SSO (`/sso?token=...`).
- **Scripts Atualizados**: `start_all.bat` sobe todos os serviços (Hub:5000, API:8000, Front:3000).
- **Frontend Verificado**: O build do Next.js (`npm run build`) está passando 100%.

## 🔑 Credenciais de Desenvolvimento
Para rodar localmente, o sistema usa um fallback de "admin provisório" quando o BigQuery não está acessível:
- **Login:** `admin@taxbase.com.br`
- **Senha:** `admin123`

## 📂 Mapa da Mina
- **`context.md` (Raiz)**: Visão de arquitetura e stack.
- **`INTEGRATION_GUIDE.md`**: Como criar módulos novos.
- **`start_all.bat`**: Como rodar tudo.
- **`service_account.json`**: Deve existir na raiz E dentro de `metricas-onvio/` (para o backend local).

## 📝 Próximos Passos Sugeridos
1. **Validar Deploy**: Planejar o deploy desta nova estrutura no Cloud Run (os Dockerfiles precisam ser revisados para os novos caminhos).
2. **Limpeza**: Verificar se o `_legacy/` ainda é útil ou pode ser arquivado em outro lugar.
3. **Novos Módulos**: Seguir o `INTEGRATION_GUIDE.md` para acoplar novas ferramentas.

Boa sorte! 🚀
