#!/usr/bin/env bash
set -euo pipefail

# Load repository-local environment variables for development.
# The file is intentionally gitignored so local machines can diverge.
load_local_env() {
  local root_dir="$1"
  local env_file="$root_dir/.env.local"

  if [ ! -f "$env_file" ]; then
    return 0
  fi

  # shellcheck disable=SC1090
  set -a
  source "$env_file"
  set +a
}
