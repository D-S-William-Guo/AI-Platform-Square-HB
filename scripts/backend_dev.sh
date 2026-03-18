#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/load_app_env.sh"
load_app_env "$ROOT_DIR"

if [ ! -d "$VENV_DIR" ]; then
  bash "$ROOT_DIR/scripts/backend_install.sh"
fi

APP_HOST="${APP_HOST:-0.0.0.0}"
BACKEND_DEV_PORT="${BACKEND_DEV_PORT:-8000}"

cd "$ROOT_DIR/backend"
PYTHONPATH=. "$VENV_DIR/bin/alembic" upgrade head
"$VENV_DIR/bin/uvicorn" app.main:app --reload --host "$APP_HOST" --port "$BACKEND_DEV_PORT"
