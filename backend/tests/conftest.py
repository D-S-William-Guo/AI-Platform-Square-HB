import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import SQLAlchemyError


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DATABASE_URL = (
    "mysql+pymysql://ai_app_user:ai_app_password@127.0.0.1:13306/ai_app_square_test?charset=utf8mb4"
)


def _quoted(identifier: str) -> str:
    return f"`{identifier.replace('`', '``')}`"


def _literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def _admin_url_for(url: URL) -> URL:
    root_password = os.getenv("MYSQL_ROOT_PASSWORD")
    if root_password:
        return url.set(username="root", password=root_password, database="mysql")
    return url.set(database="mysql")


def _ensure_test_database_exists(url: URL) -> None:
    target_engine = create_engine(
        url.render_as_string(hide_password=False),
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    try:
        with target_engine.connect():
            return
    except SQLAlchemyError:
        pass
    finally:
        target_engine.dispose()

    admin_engine = create_engine(
        _admin_url_for(url).render_as_string(hide_password=False),
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    try:
        with admin_engine.begin() as connection:
            connection.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS {_quoted(url.database)} "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            )
            if url.username and url.username != "root":
                username_literal = _literal(url.username)
                password = url.password or ""
                for host in ("%", "localhost"):
                    host_literal = _literal(host)
                    connection.execute(
                        text(
                            f"CREATE USER IF NOT EXISTS {username_literal}@{host_literal} "
                            "IDENTIFIED BY :password"
                        ),
                        {"password": password},
                    )
                    connection.execute(
                        text(
                            f"GRANT ALL PRIVILEGES ON {_quoted(url.database)}.* "
                            f"TO {username_literal}@{host_literal}"
                        )
                    )
                connection.execute(text("FLUSH PRIVILEGES"))
    finally:
        admin_engine.dispose()


def _reset_test_database(url: URL) -> None:
    target_engine = create_engine(
        url.render_as_string(hide_password=False),
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    try:
        with target_engine.begin() as connection:
            connection.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            table_names = [row[0] for row in connection.execute(text("SHOW TABLES")).all()]
            for table_name in table_names:
                connection.execute(text(f"DROP TABLE IF EXISTS {_quoted(table_name)}"))
            connection.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    finally:
        target_engine.dispose()


def _alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


os.environ.setdefault("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    """
    Rebuild the dedicated MySQL test database with Alembic, then load deterministic
    seed data required by the API tests.
    """
    test_url = make_url(os.environ["TEST_DATABASE_URL"])
    _ensure_test_database_exists(test_url)
    _reset_test_database(test_url)
    command.upgrade(_alembic_config(test_url.render_as_string(hide_password=False)), "head")

    from app.database import SessionLocal
    from app.seed import seed_base_data, seed_demo_data

    db = SessionLocal()
    try:
        seed_base_data(db)
        seed_demo_data(db)
    finally:
        db.close()

    yield


@pytest.fixture(autouse=True)
def _reset_runtime_guards():
    from app.main import clear_rate_limit_state

    clear_rate_limit_state()
    yield
    clear_rate_limit_state()
