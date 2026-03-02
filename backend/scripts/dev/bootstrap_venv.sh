#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ ! -f "${BACKEND_DIR}/requirements.txt" ]]; then
  echo "[bootstrap] ERROR: requirements.txt not found in ${BACKEND_DIR}" >&2
  exit 1
fi

cd "${BACKEND_DIR}"
echo "[bootstrap] backend dir: ${BACKEND_DIR}"

if [[ ! -d ".venv" ]]; then
  echo "[bootstrap] creating .venv"
  python -m venv .venv
else
  echo "[bootstrap] reusing existing .venv"
fi

echo "[bootstrap] activating .venv"
source .venv/bin/activate

echo "[bootstrap] installing requirements"
python -m pip install -r requirements.txt

echo "[bootstrap] installing editable package"
python -m pip install -e .

echo "[bootstrap] done"
