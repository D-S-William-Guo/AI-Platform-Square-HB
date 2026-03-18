#!/usr/bin/env bash
set -euo pipefail

abort_if_legacy_env_local_exists() {
  local root_dir="$1"
  local legacy_file="$root_dir/.env.local"

  if [ ! -f "$legacy_file" ]; then
    return 0
  fi

  cat >&2 <<'EOF'
Legacy root .env.local is no longer supported.
Move any application variables into backend/.env, keep only Docker Compose MySQL variables in root .env, then delete .env.local.
EOF
  exit 1
}

validate_compose_env_file() {
  local root_dir="$1"
  local compose_env="$root_dir/.env"
  local line=""
  local line_no=0
  local trimmed=""
  local key=""

  if [ ! -f "$compose_env" ]; then
    return 0
  fi

  while IFS= read -r line || [ -n "$line" ]; do
    line_no=$((line_no + 1))
    trimmed="${line#"${line%%[![:space:]]*}"}"

    if [ -z "$trimmed" ] || [[ "$trimmed" == \#* ]]; then
      continue
    fi

    if [[ ! "$trimmed" =~ ^(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)= ]]; then
      echo "Unsupported line in root .env at ${line_no}. Use simple KEY=value entries only." >&2
      exit 1
    fi

    key="${BASH_REMATCH[2]}"
    case "$key" in
      MYSQL_ROOT_PASSWORD|MYSQL_DATABASE|MYSQL_USER|MYSQL_PASSWORD)
        ;;
      *)
        echo "Root .env may only contain Docker Compose MySQL variables. Move ${key} to backend/.env." >&2
        exit 1
        ;;
    esac
  done < "$compose_env"
}

source_env_file() {
  local env_file="$1"

  if [ ! -f "$env_file" ]; then
    return 0
  fi

  # shellcheck disable=SC1090
  set -a
  source "$env_file"
  set +a
}

require_backend_env_file() {
  local root_dir="$1"
  local backend_env="$root_dir/backend/.env"

  if [ -f "$backend_env" ]; then
    return 0
  fi

  echo "backend/.env is required. Copy backend/.env.example to backend/.env and configure it before running app commands." >&2
  exit 1
}

load_app_env() {
  local root_dir="$1"

  abort_if_legacy_env_local_exists "$root_dir"
  validate_compose_env_file "$root_dir"
  source_env_file "$root_dir/.env"
  require_backend_env_file "$root_dir"
  source_env_file "$root_dir/backend/.env"
}
