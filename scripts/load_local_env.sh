#!/usr/bin/env bash
set -euo pipefail

# Load repository-local environment variables for development.
# `.env` is primarily used by docker compose; `.env.local` is the user override.
load_local_env() {
  local root_dir="$1"
  local env_file

  for env_file in "$root_dir/.env" "$root_dir/.env.local"; do
    if [ ! -f "$env_file" ]; then
      continue
    fi

    # shellcheck disable=SC1090
    set -a
    source "$env_file"
    set +a
  done
}
