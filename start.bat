@echo off
rem InfraSight: installs on first run, then starts the site on http://localhost:8000
cd /d "%~dp0backend"
if not exist .venv\Scripts\python.exe (
  echo Creating the Python environment, first run only...
  python -m venv .venv || goto :fail
)
.venv\Scripts\python -m pip install -q --disable-pip-version-check -r requirements.txt || goto :fail
if not exist .env (
  .venv\Scripts\python -c "import secrets,pathlib;s=pathlib.Path('.env.example').read_text();s=s.replace('SECRET_KEY=','SECRET_KEY='+secrets.token_hex(32)).replace('DEMO_PASSWORD=','DEMO_PASSWORD=demo1234');pathlib.Path('.env').write_text(s)" || goto :fail
  echo Created backend\.env - put your META_API_KEY in it, then run start.bat again.
)
echo.
echo   InfraSight: open http://localhost:8000
echo   Demo logins: citizen / tech / elected, password from DEMO_PASSWORD in backend\.env
echo   Stop with Ctrl+C
echo.
.venv\Scripts\python -m uvicorn app.main:app --port 8000
goto :eof
:fail
echo Setup failed. Is Python 3.10+ installed and on PATH?
pause
