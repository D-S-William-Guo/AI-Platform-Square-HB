#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_PATH="$ROOT_DIR/deploy/systemd/ai-platform-square.service"
SYSTEMD_DIR="${SYSTEMD_DIR:-/etc/systemd/system}"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/service_lib.sh"

SERVICE_NAME="$(service_name)"
RUN_USER="${SERVICE_RUN_USER:-${SUDO_USER:-$USER}}"
TARGET_PATH="$SYSTEMD_DIR/$SERVICE_NAME.service"
TMP_FILE="$(mktemp)"

cleanup() {
  rm -f "$TMP_FILE"
}

trap cleanup EXIT

sed \
  -e "s|__ROOT_DIR__|$ROOT_DIR|g" \
  -e "s|__RUN_USER__|$RUN_USER|g" \
  "$TEMPLATE_PATH" > "$TMP_FILE"

run_privileged install -m 0644 "$TMP_FILE" "$TARGET_PATH"
run_privileged systemctl daemon-reload
run_privileged systemctl enable "$SERVICE_NAME"

echo "Installed systemd service: $TARGET_PATH"
echo "Run user: $RUN_USER"
echo "Start it with: make service-start"
