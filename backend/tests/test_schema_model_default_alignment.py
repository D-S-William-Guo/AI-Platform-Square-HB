from app.models import App
from app.schemas import GroupAppCreate


def test_group_app_create_defaults_align_with_app_model_defaults():
    payload = {
        "name": "测试应用",
        "org": "测试单位",
        "category": "办公协同",
        "description": "用于验证 schema 与 model 默认值一致",
    }

    model = GroupAppCreate.model_validate(payload)

    difficulty_default = App.__table__.c.difficulty.default.arg
    effectiveness_type_default = App.__table__.c.effectiveness_type.default.arg

    assert model.difficulty == difficulty_default
    assert model.effectiveness_type == effectiveness_type_default
