from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_pool_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle_seconds,
    pool_use_lifo=True,
    connect_args={
        "connect_timeout": settings.db_connect_timeout,
        "read_timeout": settings.db_read_timeout,
        "write_timeout": settings.db_write_timeout,
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database_schema_ready() -> None:
    # Import models lazily so Base.metadata is fully populated without a circular import.
    from . import models  # noqa: F401

    expected_tables = set(Base.metadata.tables)
    try:
        with engine.connect() as connection:
            existing_tables = set(inspect(connection).get_table_names())
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "Failed to connect to MySQL with the configured DATABASE_URL."
        ) from exc

    missing_tables = sorted(expected_tables - existing_tables)
    if missing_tables:
        raise RuntimeError(
            "Database schema is incomplete. Missing tables: "
            f"{', '.join(missing_tables)}. Run `alembic upgrade head` before starting the app."
        )
