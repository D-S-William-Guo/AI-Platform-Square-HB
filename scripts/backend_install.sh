#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/load_pip_env.sh"
load_pip_install_args "$ROOT_DIR"

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/pip" install "${PIP_INSTALL_ARGS[@]}" -r "$ROOT_DIR/backend/requirements.txt"
if ! "$VENV_DIR/bin/pip" install "${PIP_INSTALL_ARGS[@]}" -e "$ROOT_DIR/backend"; then
  echo "Editable install with build isolation failed; retrying without build isolation." >&2
  "$VENV_DIR/bin/pip" install "${PIP_INSTALL_ARGS[@]}" --no-build-isolation -e "$ROOT_DIR/backend"
fi
