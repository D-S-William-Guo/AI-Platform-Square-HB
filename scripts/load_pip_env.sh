#!/usr/bin/env bash
set -euo pipefail

DEFAULT_PIP_INDEX_URL_PRODUCTION="http://136.142.12.68/simple/"
DEFAULT_PIP_TRUSTED_HOST_PRODUCTION="136.142.12.68"

source_backend_env_if_present() {
  local root_dir="$1"
  local backend_env="$root_dir/backend/.env"
  local had_environment="${ENVIRONMENT+x}"
  local had_pip_index="${PIP_INDEX_URL_PRODUCTION+x}"
  local had_pip_trusted_host="${PIP_TRUSTED_HOST_PRODUCTION+x}"
  local environment_value="${ENVIRONMENT-}"
  local pip_index_value="${PIP_INDEX_URL_PRODUCTION-}"
  local pip_trusted_host_value="${PIP_TRUSTED_HOST_PRODUCTION-}"

  if [[ ! -f "$backend_env" ]]; then
    return 0
  fi

  # shellcheck disable=SC1090
  set -a
  source "$backend_env"
  set +a

  if [[ -n "$had_environment" ]]; then
    ENVIRONMENT="$environment_value"
  fi

  if [[ -n "$had_pip_index" ]]; then
    PIP_INDEX_URL_PRODUCTION="$pip_index_value"
  fi

  if [[ -n "$had_pip_trusted_host" ]]; then
    PIP_TRUSTED_HOST_PRODUCTION="$pip_trusted_host_value"
  fi
}

load_pip_install_args() {
  local root_dir="$1"

  source_backend_env_if_present "$root_dir"

  local environment="${ENVIRONMENT:-development}"
  case "$environment" in
    development)
      PIP_INSTALL_ARGS=()
      unset PIP_INDEX_URL
      unset PIP_TRUSTED_HOST
      ;;
    production)
      local pip_index_url="${PIP_INDEX_URL_PRODUCTION:-$DEFAULT_PIP_INDEX_URL_PRODUCTION}"
      local pip_trusted_host="${PIP_TRUSTED_HOST_PRODUCTION:-$DEFAULT_PIP_TRUSTED_HOST_PRODUCTION}"
      PIP_INSTALL_ARGS=(-i "$pip_index_url" --trusted-host "$pip_trusted_host")
      export PIP_INDEX_URL="$pip_index_url"
      export PIP_TRUSTED_HOST="$pip_trusted_host"
      ;;
    *)
      echo "Unsupported ENVIRONMENT='$environment'. Expected 'development' or 'production'." >&2
      exit 1
      ;;
  esac
}
