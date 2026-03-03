#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/backend/.venv"

if [ ! -d "$VENV_DIR" ]; then
  bash "$ROOT_DIR/scripts/backend_install.sh"
fi

cd "$ROOT_DIR/backend"
"$VENV_DIR/bin/uvicorn" app.main:app --reload
