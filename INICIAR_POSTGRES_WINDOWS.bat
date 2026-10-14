@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo   EV CHARGEOPS - POSTGRESQL (DOCKER DESKTOP)
echo =======================================================
where docker >nul 2>&1
if errorlevel 1 (echo Docker Desktop nao encontrado.&goto :erro)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv ".venv"
  if errorlevel 1 goto :erro
)
".venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :erro
docker compose -f docker-compose.sprint2.yml up -d --wait
if errorlevel 1 goto :erro
set "DATABASE_URL=postgresql+psycopg://chargeops:chargeops_local@localhost:5432/chargeops"
cd /d "%~dp0backend"
"%~dp0.venv\Scripts\python.exe" -m app.seed_history
if errorlevel 1 goto :erro
start "EV ChargeOps API PostgreSQL" /D "%~dp0backend" "%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
start "EV ChargeOps Frontend" /D "%~dp0frontend" "%~dp0.venv\Scripts\python.exe" -m http.server 5173 --bind 127.0.0.1
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:5173/"
echo http://127.0.0.1:5173/
echo Encerrar janelas da API e interface para finalizar a demonstracao.
pause
exit /b 0
:erro
echo.
echo ERRO: verifique Python, Docker Desktop ligado e a porta 5432 livre.
pause
exit /b 1
