#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/service_lib.sh"

SERVICE_NAME="$(service_name)"
run_privileged systemctl stop "$SERVICE_NAME"
echo "Stopped service: $SERVICE_NAME"
