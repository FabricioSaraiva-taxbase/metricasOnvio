@echo off
echo ==========================================
echo    TAXBASE PLATFORM - TODOS OS SERVICOS
echo ==========================================

REM Diretório raiz do projeto
set ROOT_DIR=%~dp0

echo [1/3] Iniciando Hub Taxbase (Flask - Porta 5000)...
start "Hub Taxbase (Porta 5000)" "%ROOT_DIR%hub\run_hub.bat"

echo Aguardando 3 segundos...
timeout /t 3 /nobreak >nul

echo [2/3] Iniciando Backend Metricas (FastAPI - Porta 8000)...
if not exist "%ROOT_DIR%metricas-onvio\.venv" (
    echo    [!] Venv nao encontrado. Instalando dependencias...
    cd /d "%ROOT_DIR%metricas-onvio"
    py -3.13 -m venv .venv
    call .venv\Scripts\activate
    pip install -r backend/requirements.txt
    deactivate
    cd /d "%ROOT_DIR%"
)
start "Metricas API (Porta 8000)" cmd /k "cd /d %ROOT_DIR%metricas-onvio && py -3.13 -m uvicorn backend.main:app --reload"

echo Aguardando 5 segundos para o backend subir...
timeout /t 5 /nobreak >nul

echo [3/3] Iniciando Frontend Metricas (Next.js - Porta 3000)...
start "Metricas Frontend (Porta 3000)" "%ROOT_DIR%metricas-onvio\frontend\run_frontend.bat"

echo ==========================================
echo    TODOS OS SERVICOS INICIADOS!
echo.
echo    Hub Taxbase:   http://localhost:5000
echo    Metricas API:  http://localhost:8000/docs
echo    Metricas Web:  http://localhost:3000
echo.
echo    Fluxo de teste:
echo    1. Acesse http://localhost:5000
echo    2. Faca login no Hub
echo    3. Clique em "Metricas Onvio"
echo ==========================================
pause
