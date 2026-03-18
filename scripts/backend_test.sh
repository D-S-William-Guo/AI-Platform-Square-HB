#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"

# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/load_local_env.sh"
load_local_env "$ROOT_DIR"

if [ ! -d "$VENV_DIR" ]; then
  bash "$ROOT_DIR/scripts/backend_install.sh"
fi

MYSQL_USER="${MYSQL_USER:-ai_app_user}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-ai_app_password}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:-password}"
export MYSQL_ROOT_PASSWORD
export TEST_DATABASE_URL="${TEST_DATABASE_URL:-mysql+pymysql://${MYSQL_USER}:${MYSQL_PASSWORD}@127.0.0.1:13306/ai_app_square_test?charset=utf8mb4}"
export DATABASE_URL="$TEST_DATABASE_URL"

if [[ "$TEST_DATABASE_URL" == *"127.0.0.1:13306"* ]] || [[ "$TEST_DATABASE_URL" == *"localhost:13306"* ]]; then
  docker compose up -d mysql

  "$VENV_DIR/bin/python" - <<'PY'
import os
import time

import pymysql
from sqlalchemy.engine import make_url

url = make_url(os.environ["TEST_DATABASE_URL"])
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
    except Exception as exc:  # pragma: no cover - script bootstrap path
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
fi

cd "$ROOT_DIR/backend"
PYTHONPATH=. "$VENV_DIR/bin/pytest" tests
