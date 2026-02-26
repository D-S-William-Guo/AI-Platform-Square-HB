import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    """
    Ensure DB tables exist for tests.

    In CI we usually run against SQLite (default in settings or via env).
    Creating tables here keeps tests self-contained and reproducible.
    """
    # If the app supports DATABASE_URL override, keep it deterministic for tests.
    # Only set when not already provided by environment.
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    yield
