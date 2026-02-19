# Handoff Package

## 📧 Email Draft
**Subject:** Atualização Taxbase Platform: Integração Hub + Métricas (Monorepo)

Fala [Nome],

Seguem os arquivos atualizados do projeto **Taxbase Platform**.

**Resumo das entregas:**
1. **Integração Completa:** O "Métricas ONVIO" agora roda 100% integrado ao Hub Taxbase com autenticação unificada (SSO).
2. **Reestruturação:** Organizei o monorepo em pastas segregadas (`hub/`, `metricas-onvio/`) para facilitar a manutenção e deploy.
3. **Fixes Críticos:** Estabilizei o ambiente de desenvolvimento (Next.js), corrigi o loop de login e criei os Dockerfiles separados.

O guia técnico completo das mudanças está abaixo. É só descompactar e rodar o `start_all.bat`.

Abraço!

---

## 🛠️ Guia Técnico das Mudanças

### 1. Nova Estrutura de Pastas (Monorepo)
O projeto migrou de uma arquitetura "flat" para modulos independentes:
- **`hub/`**: O sistema legado (Flask) que gerencia autenticação (Porta 5000).
- **`metricas-onvio/`**: O novo módulo de dashboard.
  - `backend/`: API Python/FastAPI (Porta 8000).
  - `frontend/`: Interface Next.js (Porta 3000).

### 2. Estabilidade e Performance
- **Next.js Stable (v15.1.7):** Downgrade estratégico da versão Canary (16.x) para corrigir incompatibilidades com o Windows (Turbopack Panic).
- **SSO Fix:** Correção definitiva do "loop de login" através de gerenciamento atômico de estado no `AuthProvider`.
- **Zombie Process Cleanup:** Scripts para garantir que as portas 3000/8000 sejam liberadas corretamente ao reiniciar.

### 3. Deploy (Cloud Run Ready)
Adicionados arquivos de configuração para deploy robusto:
- `cloudbuild_backend.yaml` / `frontend`: Configuração explícita de build.
- `.gcloudignore`: Otimização de upload (<1MB).
- `Dockerfile.frontend`: Build otimizado (Standalone mode).

### 4. Como Rodar Localmente
Basta executar o script na raiz do projeto:
```bash
./start_all.bat
```
Isso iniciará todos os 3 serviços (Hub, API, Frontend) simultaneamente e abrirá o navegador.
