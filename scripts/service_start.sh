#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/service_lib.sh"

SERVICE_NAME="$(service_name)"
run_privileged systemctl start "$SERVICE_NAME"
run_privileged systemctl status --no-pager "$SERVICE_NAME"
