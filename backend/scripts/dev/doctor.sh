#!/usr/bin/env bash
set -euo pipefail

# backend/scripts/dev/doctor.sh
# Usage:
#   bash backend/scripts/dev/doctor.sh
# Optional env:
#   TEST_DATABASE_URL=mysql+pymysql://ai_app_user:ai_app_password@127.0.0.1:13306/ai_app_square_test?charset=utf8mb4
#   DEV_VENV=/path/to/venv   (optional override)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

# shellcheck disable=SC1091
source "${ROOT_DIR}/scripts/load_app_env.sh"
load_app_env "${ROOT_DIR}"

section () { echo -e "\n==================== $* ====================\n"; }
ok () { echo "✅ $*"; }
warn () { echo "⚠️  $*"; }
fail () { echo "❌ $*"; exit 1; }

# Prefer venv python:
# 1) explicit DEV_VENV
# 2) current activated VIRTUAL_ENV
# 3) repo local .venv
# 4) legacy backend/.venv
# 5) standardized BigData venv (ai-platform-square-hb)
# 6) fallback python/python3 from PATH
PY_CMD=""

pick_venv_py() {
  local venv="$1"
  if [[ -n "${venv}" && -x "${venv}/bin/python" ]]; then
    PY_CMD="${venv}/bin/python"
    return 0
  fi
  return 1
}

# 1) DEV_VENV override
pick_venv_py "${DEV_VENV:-}" || true

# 2) already activated venv
if [[ -z "${PY_CMD}" ]]; then
  pick_venv_py "${VIRTUAL_ENV:-}" || true
fi

# 3) repo local .venv
if [[ -z "${PY_CMD}" ]]; then
  pick_venv_py "${ROOT_DIR}/.venv" || true
fi

# 4) legacy backend/.venv
if [[ -z "${PY_CMD}" ]]; then
  pick_venv_py "${BACKEND_DIR}/.venv" || true
fi

# 5) BigData standardized venv
if [[ -z "${PY_CMD}" ]]; then
  pick_venv_py "/home/ctyun/BigData/.venvs/ai-platform-square-hb" || true
fi

# 6) fallback system python
if [[ -z "${PY_CMD}" ]]; then
  if command -v python >/dev/null 2>&1; then
    PY_CMD="$(command -v python)"
  elif command -v python3 >/dev/null 2>&1; then
    PY_CMD="$(command -v python3)"
  else
    fail "python not found in PATH"
  fi
fi

MYSQL_USER="${MYSQL_USER:-ai_app_user}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-ai_app_password}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-password}"
export MYSQL_ROOT_PASSWORD
export TEST_DATABASE_URL="${TEST_DATABASE_URL:-mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@127.0.0.1:13306/ai_app_square_test?charset=utf8mb4}"
export DATABASE_URL="${DATABASE_URL:-$TEST_DATABASE_URL}"

section "0) Location sanity"
echo "ROOT_DIR   = ${ROOT_DIR}"
echo "BACKEND_DIR= ${BACKEND_DIR}"
test -d "${BACKEND_DIR}" || fail "backend dir not found: ${BACKEND_DIR}"

section "1) Python & pip"
echo "Using Python: ${PY_CMD}"
${PY_CMD} -V || fail "python not runnable: ${PY_CMD}"
echo "python exe: $(${PY_CMD} -c 'import sys; print(sys.executable)')"
${PY_CMD} -m pip -V || fail "pip not available: ${PY_CMD} -m pip -V"
ok "python/pip ok"

section "2) Virtualenv hint"
if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  ok "VIRTUAL_ENV=${VIRTUAL_ENV}"
else
  warn "VIRTUAL_ENV not set (doctor auto-picked a python; not necessarily activated)"
fi

section "3) Editable install check (backend package)"
${PY_CMD} -c "import app; import app.main; print('import app ok')" || fail "cannot import app (editable install missing?)"

${PY_CMD} -m pip show ai-platform-square-hb-backend >/dev/null 2>&1 \
  && ok "editable package installed (pip show ok)" \
  || warn "pip show package not found (name may differ, or not installed)"

section "4) Dependencies health"
${PY_CMD} -m pip check || fail "pip check failed"
ok "pip deps ok"

section "5) PYTHONPATH (should be empty/irrelevant now)"
echo "PYTHONPATH=${PYTHONPATH:-<empty>}"
warn "If you still rely on PYTHONPATH to run tests, editable install has not fully replaced it."

section "6) Database sanity (MySQL only)"
echo "DATABASE_URL=${DATABASE_URL}"

if [[ "$DATABASE_URL" == *"127.0.0.1:13306"* ]] || [[ "$DATABASE_URL" == *"localhost:13306"* ]]; then
  (cd "${ROOT_DIR}" && docker compose up -d mysql)
fi

pushd "${BACKEND_DIR}" >/dev/null
${PY_CMD} - <<'PY'
import os
import time

import pymysql
from sqlalchemy.engine import make_url

url = make_url(os.environ["DATABASE_URL"])
root_password = os.environ["MYSQL_ROOT_PASSWORD"]
last_error = None

for _ in range(60):
    try:
        connection = pymysql.connect(
            host=url.host or "127.0.0.1",
            port=url.port or 3306,
            user="root",
            password=root_password,
            charset="utf8mb4",
            autocommit=True,
        )
        break
    except Exception as exc:
        last_error = exc
        time.sleep(1)
else:
    raise SystemExit(f"mysql did not become ready in time: {last_error}")

database_name = (url.database or "").replace("`", "``")
with connection.cursor() as cursor:
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    if url.username and url.username != "root":
        username = url.username.replace("\\", "\\\\").replace("'", "''")
        password = (url.password or "").replace("\\", "\\\\").replace("'", "''")
        for host in ("%", "localhost"):
            escaped_host = host.replace("\\", "\\\\").replace("'", "''")
            cursor.execute(
                f"CREATE USER IF NOT EXISTS '{username}'@'{escaped_host}' "
                f"IDENTIFIED BY '{password}'"
            )
            cursor.execute(
                f"GRANT ALL PRIVILEGES ON `{database_name}`.* "
                f"TO '{username}'@'{escaped_host}'"
            )
        cursor.execute("FLUSH PRIVILEGES")
connection.close()
PY
${PY_CMD} -m alembic upgrade head
${PY_CMD} -m app.bootstrap init-base
ok "db migrated and base bootstrap complete"
popd >/dev/null

section "7) Pytest quick run"
pushd "${BACKEND_DIR}" >/dev/null
${PY_CMD} -m pytest -q tests || fail "pytest failed"
popd >/dev/null
ok "pytest ok"

section "8) Optional: backend dev port check"
if command -v ss >/dev/null 2>&1; then
  BACKEND_DEV_PORT="${BACKEND_DEV_PORT:-8000}"
  ss -ltnp | grep -q ":${BACKEND_DEV_PORT}" && warn "port ${BACKEND_DEV_PORT} is LISTENING (backend dev server running?)" || ok "port ${BACKEND_DEV_PORT} not listening"
else
  warn "ss not available; skip port check"
fi

section "DONE"
ok "environment looks healthy"
