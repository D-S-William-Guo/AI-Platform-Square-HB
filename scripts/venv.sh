#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

if [ -d "$VENV_DIR" ]; then
  echo "venv already exists: $VENV_DIR"
  exit 0
fi

python3 -m venv "$VENV_DIR"
echo "venv created: $VENV_DIR"
