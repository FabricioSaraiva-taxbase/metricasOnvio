@echo off
echo ===================================================
echo   LIMPEZA DE PROJETO PARA ENVIO (EMAIL)
echo ===================================================
echo.
echo ATENCAO: Este script vai apagar as pastas geradas automaticamente
echo para reduzir o tamanho do projeto (de ~400MB para ~2MB).
echo.
echo Pastas que serao removidas:
echo  - node_modules (Dependencias Node - Reinstalar com 'npm install')
echo  - .next (Cache de Build - Recriado com 'npm run dev')
echo  - .venv (Ambientes Virtuais Python - Recriado ao rodar start)
echo  - __pycache__ (Compilados Python)
echo.
echo Pressione QUALQUER TECLA para iniciar a limpeza...
pause >nul

echo.
echo [1/4] Removendo dependencias do Frontend (pesado)...
if exist "metricas-onvio\frontend\node_modules" (
    echo   - Deletando node_modules...
    rmdir /s /q "metricas-onvio\frontend\node_modules"
)
if exist "metricas-onvio\frontend\.next" (
    echo   - Deletando .next...
    rmdir /s /q "metricas-onvio\frontend\.next"
)

echo [2/4] Removendo Ambientes Virtuais (.venv)...
if exist ".venv" rmdir /s /q ".venv"
if exist "hub\.venv" rmdir /s /q "hub\.venv"
if exist "metricas-onvio\.venv" rmdir /s /q "metricas-onvio\.venv"

echo [3/4] Limpando caches do Python (__pycache__)...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo [4/4] Limpando logs e temporarios...
del /s /q *.log 2>nul
if exist "hub\debug_logs.txt" del "hub\debug_logs.txt"
if exist "frontend_log.txt" del "frontend_log.txt"

echo.
echo ===================================================
echo   LIMPEZA CONCLUIDA!
echo.
echo   Pode zipar a pasta agora.
echo   OBS: Se ainda estiver grande, delete a pasta .git (oculta).
echo ===================================================
pause
