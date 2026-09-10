#!/usr/bin/env bash
# Start ONLY the frontend dev server (macOS / Linux). Installs deps on first run.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/frontend"
[ -d node_modules ] || npm install
exec npm run dev
