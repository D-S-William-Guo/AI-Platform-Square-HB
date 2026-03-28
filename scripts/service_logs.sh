#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LINES="${LOG_LINES:-200}"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/service_lib.sh"

SERVICE_NAME="$(service_name)"
run_privileged journalctl -u "$SERVICE_NAME" -n "$LINES" -f
