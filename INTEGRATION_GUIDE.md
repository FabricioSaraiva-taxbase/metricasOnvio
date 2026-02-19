# Guia de Integração — Como Adicionar um Novo Módulo ao Taxbase Platform

Este guia documenta o passo a passo para integrar um novo sistema/ferramenta ao Hub Taxbase, mantendo a arquitetura modular.

---

## Pré-requisitos

- Acesso ao repositório `taxbase-platform`
- O novo módulo deve ser uma aplicação web (qualquer stack)
- O módulo deve rodar em uma porta própria (ex: 4000)

---

## Passo 1: Criar a Pasta do Módulo

Crie uma pasta irmã na raiz do repositório:

```
taxbase-platform/
├── hub/
├── metricas-onvio/
├── novo-modulo/          ← NOVO
│   ├── ...
│   └── context.md        ← Documente o contexto do módulo
```

---

## Passo 2: Implementar o Endpoint SSO (Recomendado)

Para que o Hub redirecione o usuário autenticado diretamente para o módulo, crie uma rota `/sso` que:

1. Receba o token JWT via query parameter: `/sso?token=JWT_TOKEN`
2. Decodifique o payload (não precisa validar — o Hub já validou)
3. Salve o token e dados do usuário no armazenamento local
4. Redirecione para a página principal do módulo

### Payload do JWT do Hub

```json
{
  "email": "usuario@taxbase.com.br",
  "nome": "Nome do Usuário",
  "funcao_id": "admin_master",
  "permissao": "admin_master",
  "sistemas": ["*"],
  "exp": 1739999999
}
```

### Campos importantes:
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `email` | string | Identificador único do usuário |
| `nome` | string | Nome de exibição |
| `permissao` | string | `admin_master`, `admin`, ou `usuario` |
| `sistemas` | array | IDs dos sistemas que o usuário pode acessar (`["*"]` = todos) |

### SECRET_KEY para validação (se necessário):
```
taxbase-hub-secret-2026
```
Algoritmo: `HS256`

---

## Passo 3: Registrar no Hub

### 3a. Adicionar ao `hub/sistemas_taxbase.json`:

```json
{
  "nome": "Nome do Módulo",
  "sistema_id": "NOVO_MODULO",
  "url": "http://localhost:4000/sso",
  "categoria": "Categoria",
  "desc": "Descrição curta do módulo",
  "status_manual": "Forçar Online"
}
```

### 3b. Marcar como sistema interno no Hub

Em `hub/app.py`, na função `api_listar_sistemas`, adicione o `sistema_id` à lista de internos:

```python
'is_internal': sis.get('sistema_id') in ['AUDIT_FISCAL', 'METRICAS_ONVIO', 'NOVO_MODULO']
```

Isso faz o Hub injetar o token JWT automaticamente no link de acesso.

---

## Passo 4: Atualizar `start_all.bat`

Adicione o comando de inicialização do novo módulo:

```batch
echo [4/4] Iniciando Novo Modulo (Porta 4000)...
start "Novo Modulo (Porta 4000)" cmd /k "cd /d %ROOT_DIR%novo-modulo && <comando de start>"
```

---

## Passo 5: Implementar Botão "Voltar ao Hub" (Opcional)

Adicione um botão/link na interface do módulo que redireciona para o Hub:

```
URL: http://localhost:5000  (dev)
     https://hub.taxbase.com.br  (produção)
```

Use variável de ambiente `HUB_URL` para configurar.

---

## Passo 6: Deploy (Cloud Run)

Cada módulo é deployado como um serviço separado no Cloud Run:

1. Crie um `Dockerfile` na pasta do módulo
2. Configure as variáveis de ambiente:
   - `SECRET_KEY=taxbase-hub-secret-2026`
   - `HUB_URL=https://hub-url-producao`
3. Atualize a URL no `sistemas_taxbase.json` (ou BigQuery) para a URL de produção

---

## Checklist Rápido

- [ ] Pasta criada na raiz do monorepo
- [ ] Endpoint `/sso` implementado
- [ ] Registrado em `hub/sistemas_taxbase.json`
- [ ] `sistema_id` adicionado à lista `is_internal` no `hub/app.py`
- [ ] Comando de start adicionado ao `start_all.bat`
- [ ] `context.md` do módulo criado
- [ ] Testado localmente via `start_all.bat`

---

## Referência: Módulos Existentes

| Módulo | Stack | SSO | context.md |
|--------|-------|-----|------------|
| Hub | Flask | N/A (é o provedor) | `hub/context.md` |
| Auditor Fiscal | Streamlit | Não (embutido no Hub) | — |
| Métricas Onvio | Next.js + FastAPI | Sim (`/sso`) | `metricas-onvio/context.md` |
