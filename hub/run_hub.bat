@echo off
cd /d "%~dp0"
echo [Hub] Verificando ambiente...

if exist ".venv" goto :activate
echo [Hub] Criando ambiente virtual (.venv)...
py -3.13 -m venv .venv
call .venv\Scripts\activate
echo [Hub] Instalando dependencias...
pip install -r requirements.txt
goto :run

:activate
call .venv\Scripts\activate

:run
set FLASK_APP=app
echo [Hub] Iniciando servidor Flask...
python -m flask run --port 5000 --debug
pause
