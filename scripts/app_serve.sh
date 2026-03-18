#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/load_local_env.sh"
load_local_env "$ROOT_DIR"

if [ ! -d "$VENV_DIR" ]; then
  bash "$ROOT_DIR/scripts/backend_install.sh"
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  bash "$ROOT_DIR/scripts/frontend_install.sh"
fi

if [ -z "${DATABASE_URL:-}" ] && [ ! -f "$ROOT_DIR/backend/.env" ]; then
  echo "DATABASE_URL is not configured. Set it in backend/.env or .env.local before starting the app."
  exit 1
fi

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-80}"

bash "$ROOT_DIR/scripts/frontend_build.sh"

cd "$ROOT_DIR/backend"
PYTHONPATH=. "$VENV_DIR/bin/alembic" upgrade head
PYTHONPATH=. "$VENV_DIR/bin/python" -m app.bootstrap init-base
exec "$VENV_DIR/bin/uvicorn" app.main:app --host "$APP_HOST" --port "$APP_PORT"
