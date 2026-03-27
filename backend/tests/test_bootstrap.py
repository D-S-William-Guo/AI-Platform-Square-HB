from app.auth_utils import verify_password
from app.config import settings
from app.database import SessionLocal
from app.models import User
from app.seed import reset_default_users, seed_default_users


def test_seed_default_users_keeps_existing_password_hash():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "lisi").first()
        assert user is not None
        original_hash = user.password_hash

        user.password_hash = "manually-set-hash"
        db.commit()

        seed_default_users(db)
        db.refresh(user)

        assert user.password_hash == "manually-set-hash"

        user.password_hash = original_hash
        db.commit()
    finally:
        db.close()


def test_reset_default_users_overwrites_existing_password_hash():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "lisi").first()
        assert user is not None

        original_hash = user.password_hash
        user.password_hash = "manually-set-hash"
        db.commit()

        reset_default_users(db)
        db.refresh(user)

        assert user.password_hash != "manually-set-hash"
        assert verify_password(settings.admin_default_password, user.password_hash)

        user.password_hash = original_hash
        db.commit()
    finally:
        db.close()
