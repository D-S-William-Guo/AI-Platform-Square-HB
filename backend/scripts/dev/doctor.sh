#!/usr/bin/env bash
set -euo pipefail

# backend/scripts/dev/doctor.sh
# Usage:
#   bash backend/scripts/dev/doctor.sh
# Optional env:
#   DATABASE_URL=sqlite:///./test.db
#   DEV_VENV=/path/to/venv   (optional override)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

section () { echo -e "\n==================== $* ====================\n"; }
ok () { echo "✅ $*"; }
warn () { echo "⚠️  $*"; }
fail () { echo "❌ $*"; exit 1; }

# Prefer venv python:
# 1) explicit DEV_VENV
# 2) current activated VIRTUAL_ENV
# 3) repo local backend/.venv
# 4) standardized BigData venv (ai-platform-square-hb)
# 5) fallback python/python3 from PATH
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

# 3) backend/.venv
if [[ -z "${PY_CMD}" ]]; then
  pick_venv_py "${BACKEND_DIR}/.venv" || true
fi

# 4) BigData standardized venv
if [[ -z "${PY_CMD}" ]]; then
  pick_venv_py "/home/ctyun/BigData/.venvs/ai-platform-square-hb" || true
fi

# 5) fallback system python
if [[ -z "${PY_CMD}" ]]; then
  if command -v python >/dev/null 2>&1; then
    PY_CMD="$(command -v python)"
  elif command -v python3 >/dev/null 2>&1; then
    PY_CMD="$(command -v python3)"
  else
    fail "python not found in PATH"
  fi
fi

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

section "6) Database sanity (sqlite default for tests)"
export DATABASE_URL="${DATABASE_URL:-sqlite:///./test.db}"
echo "DATABASE_URL=${DATABASE_URL}"
pushd "${BACKEND_DIR}" >/dev/null
${PY_CMD} - <<'PY'
from app.database import Base, engine
Base.metadata.create_all(bind=engine)
print("db tables ensured")
PY
ok "db tables ensured"
popd >/dev/null

section "7) Pytest quick run"
pushd "${BACKEND_DIR}" >/dev/null
${PY_CMD} -m pytest -q tests || fail "pytest failed"
popd >/dev/null
ok "pytest ok"

section "8) Optional: port 8000 check (if you run uvicorn)"
if command -v ss >/dev/null 2>&1; then
  ss -ltnp | grep -q ":8000" && warn "port 8000 is LISTENING (server running?)" || ok "port 8000 not listening"
else
  warn "ss not available; skip port check"
fi

section "DONE"
ok "environment looks healthy"
