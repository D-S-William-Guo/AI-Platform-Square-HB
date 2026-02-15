from datetime import date

from app.schemas import AppDetail


def test_app_detail_allows_nullable_ranking_fields_in_validation_and_dump():
    payload = {
        "id": 1,
        "name": "示例应用",
        "org": "示例单位",
        "section": "group",
        "category": "效率",
        "description": "用于测试 schema 兼容性",
        "status": "available",
        "monthly_calls": 123.0,
        "release_date": date(2024, 1, 1),
        "api_open": True,
        "difficulty": "Medium",
        "contact_name": "测试人",
        "highlight": "测试亮点",
        "access_mode": "direct",
        "access_url": "https://example.com",
        "target_system": "系统A",
        "target_users": "用户A",
        "problem_statement": "测试问题描述",
        "effectiveness_type": "efficiency_gain",
        "effectiveness_metric": "效率提升",
        "cover_image_url": "https://example.com/image.png",
        "ranking_enabled": None,
        "ranking_weight": None,
        "ranking_tags": None,
    }

    model = AppDetail.model_validate(payload)

    assert model.ranking_enabled is None
    assert model.ranking_weight is None
    assert model.ranking_tags is None

    dumped = model.model_dump()
    assert dumped["ranking_enabled"] is None
    assert dumped["ranking_weight"] is None
    assert dumped["ranking_tags"] is None
