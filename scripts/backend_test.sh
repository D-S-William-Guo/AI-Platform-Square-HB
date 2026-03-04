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

cd "$ROOT_DIR/backend"
PYTHONPATH=. "$VENV_DIR/bin/pytest" tests
