"""Shared test utilities for unit tests."""

from types import SimpleNamespace


def make_app(**overrides) -> SimpleNamespace:
    """Create a mock App-like object for testing."""
    defaults = dict(
        id=1, name="test-app", org="test-org", section="province",
        status="available", monthly_calls=10.0, effectiveness_type="efficiency_gain",
        difficulty="Medium", ranking_enabled=True, ranking_weight=1.0,
        ranking_tags="推荐", last_month_calls=5.0, new_users_count=100,
        search_count=200, share_count=50, favorite_count=30,
        company=None, department=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_dimension(id: int = 1, name: str = "用户满意度", **overrides) -> SimpleNamespace:
    """Create a mock RankingDimension-like object."""
    defaults = dict(
        id=id, name=name, description="description",
        calculation_method="scoring_method", weight=1.0, is_active=True,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_ranking_config(**overrides) -> SimpleNamespace:
    """Create a mock RankingConfig-like object."""
    defaults = dict(
        id="excellent", name="总应用榜", description="description",
        dimensions_config='[{"dim_id": 1, "weight": 1.0}]',
        calculation_method="composite", is_active=True,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_submission_payload(**overrides) -> SimpleNamespace:
    """Create a mock submission payload."""
    defaults = dict(
        app_name="test-app", unit_name="test-unit", contact="张三",
        contact_phone="13800138000", contact_email="test@example.com",
        category="前端市场类", scenario="This is a test scenario for the application",
        embedded_system="test-system", problem_statement="This is a problem statement",
        effectiveness_type="efficiency_gain", effectiveness_metric="efficiency_metric",
        data_level="L2", expected_benefit="Expected benefit description",
        monthly_calls=10, difficulty="Medium",
        cover_image_url="", detail_doc_url="", detail_doc_name="",
    )
    defaults.update(overrides)
    p = SimpleNamespace(**defaults)

    def model_dump():
        return defaults.copy()
    p.model_dump = model_dump
    return p
