#!/usr/bin/env bash
# InfraSight on macOS / Linux: installs on first run, then starts the site on http://localhost:8000
# (the same steps as start.bat on Windows). Usage: ./start.sh   or   bash start.sh
set -e
cd "$(dirname "$0")/backend"
PY=$(command -v python3 || command -v python) || { echo "Python 3.10+ is needed: https://www.python.org/downloads/"; exit 1; }
"$PY" -c 'import sys; sys.exit(sys.version_info < (3, 10))' || { echo "Python 3.10+ is needed (found $("$PY" -V))"; exit 1; }
if [ ! -x .venv/bin/python ]; then
  echo "Creating the Python environment, first run only..."
  "$PY" -m venv .venv
fi
.venv/bin/python -m pip install -q --disable-pip-version-check -r requirements.txt
if [ ! -f .env ]; then
  .venv/bin/python -c "import secrets,pathlib;s=pathlib.Path('.env.example').read_text();s=s.replace('SECRET_KEY=','SECRET_KEY='+secrets.token_hex(32)).replace('DEMO_PASSWORD=','DEMO_PASSWORD=demo1234');pathlib.Path('.env').write_text(s)"
  echo "Created backend/.env - put your META_API_KEY in it, then run ./start.sh again."
fi
echo
echo "  InfraSight: open http://localhost:8000"
echo "  Demo logins: citizen / tech / elected, password from DEMO_PASSWORD in backend/.env"
echo "  Stop with Ctrl+C"
echo
exec .venv/bin/python -m uvicorn app.main:app --port "${PORT:-8000}"
