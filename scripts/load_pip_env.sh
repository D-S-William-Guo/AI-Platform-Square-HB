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

ensure_python_packaging_tools() {
  local python_cmd="$1"
  local -a packages_to_install=()
  local package

  while IFS= read -r package; do
    [[ -n "$package" ]] && packages_to_install+=("$package")
  done < <("$python_cmd" - <<'PY'
import importlib.metadata as metadata

required = []

checks = (
    ("pip", None),
    ("setuptools", 68),
    ("wheel", None),
)

for package_name, min_major in checks:
    try:
        version = metadata.version(package_name)
    except metadata.PackageNotFoundError:
        required.append(package_name if min_major is None else f"{package_name}>={min_major}")
        continue

    if min_major is None:
        continue

    try:
        major = int(version.split(".", 1)[0])
    except ValueError:
        major = 0

    if major < min_major:
        required.append(f"{package_name}>={min_major}")

for package in required:
    print(package)
PY
)

  if ((${#packages_to_install[@]} > 0)); then
    "$python_cmd" -m pip install "${PIP_INSTALL_ARGS[@]}" --upgrade "${packages_to_install[@]}"
  fi
}

use_build_isolation_for_editable_install() {
  local environment="${ENVIRONMENT:-development}"
  local override="${PIP_USE_BUILD_ISOLATION:-}"

  if [[ -n "$override" ]]; then
    case "$override" in
      1|true|TRUE|yes|YES|on|ON)
        return 0
        ;;
      0|false|FALSE|no|NO|off|OFF)
        return 1
        ;;
      *)
        echo "Unsupported PIP_USE_BUILD_ISOLATION='$override'. Expected true/false." >&2
        exit 1
        ;;
    esac
  fi

  [[ "$environment" == "development" ]]
}
