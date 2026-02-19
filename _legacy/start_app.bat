@echo off
echo ==========================================
echo    INICIANDO SISTEMA METRICAS ONVIO
echo ==========================================

echo [1/2] Iniciando Backend (API)...
start "Backend API (Porta 8000)" cmd /k "py -3.13 -m uvicorn backend.main:app --reload"

echo Aguardando 5 segundos para o backend subir...
timeout /t 5 /nobreak >nul

echo [2/2] Iniciando Frontend (Next.js)...
cd frontend
start "Frontend NextJS (Porta 3000)" cmd /k "npm run dev"

echo ==========================================
echo    SISTEMA INICIADO!
echo    Acesse: http://localhost:3000
echo ==========================================
pause
