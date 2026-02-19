# Guia de Deploy (Google Cloud Run)

Como o sistema foi modernizado (Backend FastAPI + Frontend Next.js), o deploy **NÃO** pode ser feito com um único container. Siga os passos:

---

## 🏗️ Passo 1: Deploy do Backend (API)
Na pasta `metricas-onvio/` (no terminal Google Cloud SDK):

## 🏗️ Passo 1: Deploy do Backend (API)
Na pasta `metricas-onvio/` (no terminal Google Cloud SDK):

1. **Construir a imagem:**
   ```bash
   gcloud builds submit --config cloudbuild_backend.yaml .
   ```

2. **Fazer o deploy:**
   ```bash
   gcloud run deploy metricas-backend --image gcr.io/[SEU_PROJECT_ID]/metricas-backend --port 8000 --allow-unauthenticated --region us-central1
   ```
   *(Substitua `[SEU_PROJECT_ID]` pelo ID do seu projeto)*

---

## 🎨 Passo 2: Deploy do Frontend (Web)
Na pasta `metricas-onvio/`:

1. **Construir a imagem:**
   ```bash
   gcloud builds submit --config cloudbuild_frontend.yaml .
   ```

2. **Fazer o deploy:**
   ```bash
   gcloud run deploy metricas-frontend --image gcr.io/[SEU_PROJECT_ID]/metricas-frontend --port 3000 --allow-unauthenticated --region us-central1 --set-env-vars API_URL=[URL_DO_BACKEND]
   ```
   *(Substitua `[SEU_PROJECT_ID]` e `[URL_DO_BACKEND]`)*

---

## 🔗 Passo 3: Atualizar o Hub
1. Abra o arquivo `hub/sistemas_taxbase.json` (ou configure nas Variáveis de Ambiente do Hub se estiver usando).
2. Atualize a URL do item "Métricas Onvio" para apontar para o Frontend (`https://metricas-frontend-123.run.app/sso`).
3. Faça o Re-deploy do Hub:
   ```bash
   gcloud run deploy hub-taxbase --source . --port 5000
   ```

---

## 🚫 Solução de Problemas

### 1. Erro: `PERMISSION_DENIED` ou `Forbidden`
Indica que sua conta não tem permissão para tornar o serviço público.
**Solução:** Peça a um administrador do projeto para rodar:
```bash
gcloud run services add-iam-policy-binding [NOME_DO_SERVICO] --member="allUsers" --role="roles/run.invoker" --region=us-central1
```

### 2. Avisos no Build (NPM Warn)
Alertas como `npm warn EBADENGINE` (versão do Node) ou `deprecated` são normais e não impedem o funcionamento. Pode ignorar se o final mostrar `SUCCESS`.

### 3. "Cloud Build API not enabled"
Se for a primeira vez, digite `y` para ativar a API quando solicitado.
