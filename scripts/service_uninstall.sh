#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYSTEMD_DIR="${SYSTEMD_DIR:-/etc/systemd/system}"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/service_lib.sh"

SERVICE_NAME="$(service_name)"
TARGET_PATH="$SYSTEMD_DIR/$SERVICE_NAME.service"

if run_privileged test -f "$TARGET_PATH"; then
  run_privileged systemctl stop "$SERVICE_NAME" || true
  run_privileged systemctl disable "$SERVICE_NAME" || true
  run_privileged rm -f "$TARGET_PATH"
  run_privileged systemctl daemon-reload
  echo "Removed systemd service: $TARGET_PATH"
else
  echo "Systemd service file not found: $TARGET_PATH"
fi
