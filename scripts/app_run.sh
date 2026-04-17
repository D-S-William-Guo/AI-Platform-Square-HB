#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
FRONTEND_INDEX="$ROOT_DIR/frontend/dist/index.html"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/load_app_env.sh"
load_app_env "$ROOT_DIR"

if [ ! -f "$FRONTEND_INDEX" ]; then
  cat >&2 <<'EOF'
frontend/dist is missing.
Build the frontend on a development machine first, package the deployment artifact with frontend/dist included, then retry remote startup.
EOF
  exit 1
fi

if [ ! -d "$VENV_DIR" ] || [ ! -x "$VENV_DIR/bin/python" ] || [ ! -x "$VENV_DIR/bin/alembic" ] || [ ! -x "$VENV_DIR/bin/uvicorn" ]; then
  cat >&2 <<'EOF'
Backend runtime environment is missing.
Run 'make venv' and 'make backend-install' on the deployment host before starting the app.
EOF
  exit 1
fi

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-80}"
UVICORN_WORKERS="${UVICORN_WORKERS:-2}"

cd "$ROOT_DIR/backend"
PYTHONPATH=. "$VENV_DIR/bin/alembic" upgrade head
PYTHONPATH=. "$VENV_DIR/bin/python" -m app.bootstrap init-base
exec "$VENV_DIR/bin/uvicorn" app.main:app --host "$APP_HOST" --port "$APP_PORT" --workers "$UVICORN_WORKERS"
