#!/usr/bin/env bash
# BorderGuard AI — one-command local startup for macOS / Linux.
# Creates the backend venv (if missing), installs deps, then runs the backend
# (:8000) and frontend (:5173) together. Ctrl-C stops both.
#
# First run needs internet (pip + npm). For an OFFLINE demo, run once online,
# then also run:  (cd backend && source .venv/bin/activate && python -m app.preload)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-python3}"

echo "==> BorderGuard AI starting..."
command -v "$PYTHON" >/dev/null || { echo "ERROR: $PYTHON not found. Install Python 3.11."; exit 1; }
command -v node >/dev/null || { echo "ERROR: node not found. Install Node.js LTS."; exit 1; }

# --- Backend ---------------------------------------------------------------
if [ ! -d "backend/.venv" ]; then
  echo "==> Creating backend virtual environment..."
  "$PYTHON" -m venv backend/.venv
fi
# shellcheck disable=SC1091
source backend/.venv/bin/activate
echo "==> Installing backend dependencies..."
python -m pip install --upgrade pip >/dev/null
pip install -r backend/requirements.txt

# --- Frontend --------------------------------------------------------------
if [ ! -d "frontend/node_modules" ]; then
  echo "==> Installing frontend dependencies..."
  (cd frontend && npm install)
fi

# --- Run both --------------------------------------------------------------
echo "==> Launching backend (:8000) and frontend (:5173). Press Ctrl-C to stop."
(cd backend && exec uvicorn app.main:app --port 8000) &
BACKEND_PID=$!
trap 'echo; echo "==> Stopping..."; kill "$BACKEND_PID" 2>/dev/null || true' EXIT INT TERM

(cd frontend && npm run dev)
