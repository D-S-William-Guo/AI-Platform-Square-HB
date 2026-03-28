#!/usr/bin/env bash
set -euo pipefail

DEFAULT_SERVICE_NAME="ai-platform-square"

service_name() {
  printf '%s' "${SERVICE_NAME:-$DEFAULT_SERVICE_NAME}"
}

run_privileged() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  else
    sudo "$@"
  fi
}
