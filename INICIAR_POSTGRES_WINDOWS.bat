@echo off
setlocal
cd /d "%~dp0"
where docker >nul 2>&1 || (echo Docker Desktop necessario & pause & exit /b 1)
docker compose -f docker-compose.sprint2.yml up -d --wait || (pause & exit /b 1)
if not exist .venv py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt || (pause & exit /b 1)
set "DATABASE_URL=postgresql+psycopg://chargeops:chargeops_local@localhost:5432/chargeops"
cd backend
..\.venv\Scripts\python.exe -m app.seed_history || (pause & exit /b 1)
start "EV ChargeOps API" cmd /k "..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
cd ..\frontend
start "EV ChargeOps Web" cmd /k "py -3 -m http.server 5173 --bind 127.0.0.1"
timeout /t 3 >nul
start http://127.0.0.1:5173/
pause
