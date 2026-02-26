import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    """
    Ensure DB tables exist AND seed initial data for API tests.

    CI uses a fresh environment; without seeding, /api/apps will return [].
    """
    os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

    from app.database import Base, engine, SessionLocal

    # create tables
    Base.metadata.create_all(bind=engine)

    # seed data (idempotent: seed_data returns if App/Submission already exist)
    db = SessionLocal()
    try:
        from app.seed import seed_data
        seed_data(db)
    finally:
        db.close()

    yield
