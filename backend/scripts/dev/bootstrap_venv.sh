#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -f "${BACKEND_DIR}/requirements.txt" ]]; then
  echo "[bootstrap] ERROR: requirements.txt not found in ${BACKEND_DIR}" >&2
  exit 1
fi

cd "${BACKEND_DIR}"
echo "[bootstrap] backend dir: ${BACKEND_DIR}"
echo "[bootstrap] repo root: ${ROOT_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[bootstrap] creating ${VENV_DIR} (ensure python venv support is installed, e.g. python3-venv/ensurepip)"
  python -m venv "${VENV_DIR}" || { echo "[bootstrap] ERROR: failed to create ${VENV_DIR} (missing python3-venv/ensurepip?)" >&2; exit 1; }
else
  echo "[bootstrap] reusing existing ${VENV_DIR}"
fi

VENV_PY="${VENV_DIR}/bin/python"
if [[ ! -x "${VENV_PY}" ]]; then
  echo "[bootstrap] ERROR: venv python not executable: ${VENV_PY}" >&2
  exit 1
fi

echo "[bootstrap] installing requirements"
"${VENV_PY}" -m pip install -r requirements.txt

echo "[bootstrap] installing editable package"
"${VENV_PY}" -m pip install -e .

echo "[bootstrap] done"
