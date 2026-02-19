# Deploy HubTaxbase to Google Cloud Run

This guide will help you deploy the **HubTaxbase** application to Google Cloud Run.

## Prerequisites

1.  **Google Cloud SDK**: Ensure `gcloud` is installed and authenticated.
    -   *Note: Your local `gcloud` installation seems to have permissions issues. You may need to reinstall it or run as Administrator.*
2.  **Docker**: Required to build the container image.
3.  **GCP Project**: A Google Cloud Project with billing enabled.

## Step 1: Initial Setup

Open a terminal in the project root (`HUB_TAXBASE`) and run:

```powershell
# Authenticate with Google Cloud
gcloud auth login

# Set your project ID
gcloud config set project YOUR_PROJECT_ID
```

## Step 2: Enable Required APIs

```powershell
gcloud services enable cloudbuild.googleapis.com run.googleapis.com
```

## Step 3: Deployment (Option A - Direct Source)

Cloud Run can build from source automatically:

```powershell
gcloud run deploy hubtaxbase --source . --region us-central1 --allow-unauthenticated
```
*Follow the prompts:*
-   **Region**: Select a region close to you (e.g., `southamerica-east1` for São Paulo).
-   **Service Name**: Press Enter to accept `hubtaxbase`.
-   **Allow unauthenticated invocations**: `y` (Yes) if you want it public.

## Step 4: Deployment (Option B - Docker Build)

If you prefer to build locally first:

1.  **Build the image**:
    ```powershell
    docker build -t gcr.io/YOUR_PROJECT_ID/hubtaxbase .
    ```

2.  **Push to Container Registry**:
    ```powershell
    docker push gcr.io/YOUR_PROJECT_ID/hubtaxbase
    ```

3.  **Deploy**:
    ```powershell
    gcloud run deploy hubtaxbase --image gcr.io/YOUR_PROJECT_ID/hubtaxbase --region southamerica-east1 --allow-unauthenticated
    ```

## Step 5: Service Account & Permissions

The application uses Google BigQuery. The **Cloud Run Service Account** must have permissions:

1.  Go to **Cloud Console > IAM**.
2.  Find the service account used by Cloud Run (usually `Default Compute Service Account`).
3.  Add roles:
    -   `BigQuery User`
    -   `BigQuery Data Editor`

## ⚠️ Important Notes

### Data Persistence
> **WARNING**: Files in `data/*.json` (Users, Systems) will be **RESET** every time the application restarts.
> **Solution**: For a production app, you must migrate `sistemas.json` and `usuarios.json` to a database (like Firestore or Cloud SQL) or load them from a Google Cloud Storage bucket on startup.

### Credentials
The application is configured to use **Application Default Credentials** (ADC) when running on Cloud Run. You do **NOT** need to upload `credentials.json` if the Service Account has the correct permissions.

### Environment Variables
You can set `FLASK_DEBUG=false` in Cloud Run to disable debug mode.
