#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/load_app_env.sh"
load_app_env "$ROOT_DIR"

APP_HOST="${APP_HOST:-0.0.0.0}"
BACKEND_DEV_PORT="${BACKEND_DEV_PORT:-8000}"
FRONTEND_DEV_PORT="${FRONTEND_DEV_PORT:-5173}"
export APP_HOST BACKEND_DEV_PORT FRONTEND_DEV_PORT
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://127.0.0.1:${BACKEND_DEV_PORT}}"

cd "$ROOT_DIR/frontend"
npm run dev
