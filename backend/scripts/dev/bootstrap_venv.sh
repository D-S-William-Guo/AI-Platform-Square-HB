#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

# shellcheck disable=SC1091
source "${ROOT_DIR}/scripts/load_pip_env.sh"
load_pip_install_args "${ROOT_DIR}"

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

echo "[bootstrap] upgrading pip/setuptools/wheel"
"${VENV_PY}" -m pip install "${PIP_INSTALL_ARGS[@]}" --upgrade pip "setuptools>=68" wheel

echo "[bootstrap] installing requirements"
"${VENV_PY}" -m pip install "${PIP_INSTALL_ARGS[@]}" -r requirements.txt

echo "[bootstrap] installing editable package"
if ! "${VENV_PY}" -m pip install "${PIP_INSTALL_ARGS[@]}" -e .; then
  echo "[bootstrap] editable install with build isolation failed, retrying without build isolation"
  "${VENV_PY}" -m pip install "${PIP_INSTALL_ARGS[@]}" --no-build-isolation -e .
fi

echo "[bootstrap] done"
