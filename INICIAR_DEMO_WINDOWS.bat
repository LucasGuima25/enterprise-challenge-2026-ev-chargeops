@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo   EV CHARGEOPS - DEMONSTRACAO (SEM DOCKER)
echo =======================================================
echo.
where py >nul 2>&1
if %errorlevel%==0 (set "PYCMD=py -3") else (set "PYCMD=python")
if not exist ".venv\Scripts\python.exe" (
  echo Preparando o ambiente Python...
  %PYCMD% -m venv ".venv"
  if errorlevel 1 goto :erro
)
echo Instalando ou verificando dependencias...
".venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :erro
set "DATABASE_URL=sqlite:///./demo.sqlite3"
cd /d "%~dp0backend"
echo Carregando dados ficticios...
"%~dp0.venv\Scripts\python.exe" -m app.seed_history
if errorlevel 1 goto :erro
start "EV ChargeOps API" /D "%~dp0backend" "%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
start "EV ChargeOps Frontend" /D "%~dp0frontend" "%~dp0.venv\Scripts\python.exe" -m http.server 5173 --bind 127.0.0.1
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:5173/"
echo.
echo DASHBOARD: http://127.0.0.1:5173/
echo API:       http://127.0.0.1:8000/docs
echo.
echo Se nao carregar, aguarde e clique Atualizar na pagina.
echo Modo DEMO usa SQLite local e dados ficticios. Nao demonstra PostgreSQL.
pause
exit /b 0
:erro
echo.
echo ERRO: instale Python 3.11+ e verifique conexao com internet.
pause
exit /b 1
