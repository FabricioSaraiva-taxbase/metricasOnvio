"""
Metricas ONVIO — Backend API (FastAPI)

Ponto de entrada da aplicação. Agrega todos os routers e configura CORS.
Swagger UI disponível em /docs.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.schemas import HealthResponse
from backend.routers import auth, data, admin, labels, departments
from backend.services.bigquery_service import is_bigquery_available

app = FastAPI(
    title="Metricas ONVIO API",
    description="API REST para o Dashboard de Métricas de Atendimento da Taxbase.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS (libera tudo em dev, restringir em produção) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTERS ---
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(admin.router)
app.include_router(labels.router)
app.include_router(departments.router)


# --- HEALTH CHECK ---
@app.get("/api/health", response_model=HealthResponse, tags=["Sistema"])
async def health_check():
    """Verifica se o servidor está ativo e se o BigQuery está acessível."""
    return HealthResponse(
        status="ok",
        bigquery=is_bigquery_available(),
    )
