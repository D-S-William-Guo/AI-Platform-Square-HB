import json

from app.auth_utils import verify_password
from app.config import settings
from app.database import SessionLocal
from app.models import RankingConfig, RankingDimension, User
from app.seed import reset_default_users, seed_default_users, sync_system_presets


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


def test_sync_system_presets_updates_builtin_rankings_without_touching_custom_objects():
    db = SessionLocal()
    try:
        excellent = db.query(RankingConfig).filter(RankingConfig.id == "excellent").first()
        dimension = db.query(RankingDimension).filter(RankingDimension.name == "用户满意度").first()
        assert excellent is not None
        assert dimension is not None

        custom_dimension = RankingDimension(
            name="自定义指标",
            description="custom",
            calculation_method="custom",
            weight=3.0,
            is_active=False,
        )
        db.add(custom_dimension)
        custom_config = RankingConfig(
            id="custom",
            name="自定义榜单",
            description="custom",
            dimensions_config='[]',
            calculation_method="custom",
            is_active=False,
        )
        db.add(custom_config)
        db.commit()

        dimension.weight = 9.0
        excellent.name = "旧优秀榜"
        excellent.dimensions_config = '[{"dim_id": 999, "weight": 9.9}]'
        db.commit()

        sync_system_presets(db)
        db.refresh(dimension)
        db.refresh(excellent)
        db.refresh(custom_dimension)
        db.refresh(custom_config)

        assert dimension.weight == 1.0
        assert excellent.name == "总应用榜"
        assert json.loads(excellent.dimensions_config) == [
            {"dim_id": 1, "weight": 1.0},
            {"dim_id": 2, "weight": 1.0},
            {"dim_id": 4, "weight": 1.0},
            {"dim_id": 5, "weight": 1.0},
        ]
        assert custom_dimension.weight == 3.0
        assert custom_config.name == "自定义榜单"
    finally:
        db.close()
