#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/load_local_env.sh"
load_local_env "$ROOT_DIR"

cd "$ROOT_DIR/frontend"
npm run dev
