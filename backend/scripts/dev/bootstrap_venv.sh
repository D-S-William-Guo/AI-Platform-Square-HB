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
  echo "[bootstrap] creating .venv (ensure python venv support is installed, e.g. python3-venv/ensurepip)"
  python -m venv .venv || { echo "[bootstrap] ERROR: failed to create .venv (missing python3-venv/ensurepip?)" >&2; exit 1; }
else
  echo "[bootstrap] reusing existing .venv"
fi

VENV_PY="${BACKEND_DIR}/.venv/bin/python"
if [[ ! -x "${VENV_PY}" ]]; then
  echo "[bootstrap] ERROR: venv python not executable: ${VENV_PY}" >&2
  exit 1
fi

echo "[bootstrap] installing requirements"
"${VENV_PY}" -m pip install -r requirements.txt

echo "[bootstrap] installing editable package"
"${VENV_PY}" -m pip install -e .

echo "[bootstrap] done"
