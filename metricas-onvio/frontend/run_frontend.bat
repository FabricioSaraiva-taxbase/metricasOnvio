@echo off
cd /d "%~dp0"
echo [Frontend] Verificando dependencias...

if exist "node_modules" goto :run
echo [Frontend] node_modules nao encontrado.
echo [Frontend] Instalando dependencias (isso pode demorar)...
call npm install

:run
echo [Frontend] Iniciando servidor Next.js...
npm run dev
pause
