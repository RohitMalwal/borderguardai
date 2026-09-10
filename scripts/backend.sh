#!/usr/bin/env bash
# Start ONLY the backend (macOS / Linux). Creates venv + installs on first run.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
[ -d backend/.venv ] || "$PYTHON" -m venv backend/.venv
# shellcheck disable=SC1091
source backend/.venv/bin/activate
python -m pip install --upgrade pip >/dev/null
pip install -r backend/requirements.txt
cd backend
exec uvicorn app.main:app --reload --port 8000
