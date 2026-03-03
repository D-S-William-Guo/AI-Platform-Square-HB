#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

check_cmd() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] $cmd"
  else
    echo "[MISSING] $cmd"
    return 1
  fi
}

check_cmd_warn() {
  local cmd="$1"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] $cmd"
  else
    echo "[WARN] $cmd is missing"
  fi
}

status=0

for cmd in bash make python3 docker; do
  check_cmd "$cmd" || status=1
done

check_cmd_warn npm

if ! docker compose version >/dev/null 2>&1; then
  echo "[MISSING] docker compose"
  status=1
else
  echo "[OK] docker compose"
fi

for path in backend/app/main.py backend/tests frontend/package.json docker-compose.yml; do
  if [ -e "$ROOT_DIR/$path" ]; then
    echo "[OK] $path"
  else
    echo "[MISSING] $path"
    status=1
  fi
done

if [ "$status" -ne 0 ]; then
  exit 1
fi

echo "doctor check passed"
