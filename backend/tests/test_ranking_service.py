"""Unit tests for ranking_service.py."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.ranking_service import (
    calculate_app_score,
    calculate_dimension_score,
    calculate_three_layer_score,
    collect_config_dimension_ids,
    serialize_setting_snapshot,
    validate_publish_preconditions,
    validate_submission_ranking_fields,
)

from helpers import make_app, make_dimension


# ---------------------------------------------------------------------------
# validate_submission_ranking_fields
# ---------------------------------------------------------------------------

class TestValidateSubmissionRankingFields:
    def test_valid_fields_pass(self):
        validate_submission_ranking_fields(1.0, "tag1,tag2", "[]")

    def test_weight_too_low_raises(self):
        with pytest.raises(HTTPException, match="ranking_weight must be between"):
            validate_submission_ranking_fields(0.05, "", "")

    def test_weight_too_high_raises(self):
        with pytest.raises(HTTPException, match="ranking_weight must be between"):
            validate_submission_ranking_fields(15.0, "", "")

    def test_tags_too_long_raises(self):
        with pytest.raises(HTTPException, match="ranking_tags must not exceed"):
            validate_submission_ranking_fields(1.0, "x" * 256, "")

    def test_dimensions_too_long_raises(self):
        with pytest.raises(HTTPException, match="ranking_dimensions must not exceed"):
            validate_submission_ranking_fields(1.0, "", "x" * 501)

    def test_boundary_values_pass(self):
        validate_submission_ranking_fields(0.1, "a" * 255, "a" * 500)
        validate_submission_ranking_fields(10.0, "", "")


# ---------------------------------------------------------------------------
# calculate_dimension_score
# ---------------------------------------------------------------------------

class TestCalculateDimensionScore:
    def test_user_satisfaction_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(monthly_calls=12.5), make_dimension(1, "用户满意度")
        )
        assert 0 <= score <= 500
        assert "用户满意度" in detail or "月调用量" in detail

    def test_business_value_with_revenue_growth(self):
        score, detail = calculate_dimension_score(
            make_app(effectiveness_type="revenue_growth"), make_dimension(1, "业务价值")
        )
        assert score == 100
        assert "拉动收入" in detail or "满分" in detail

    def test_business_value_with_efficiency_gain(self):
        score, detail = calculate_dimension_score(
            make_app(effectiveness_type="efficiency_gain"), make_dimension(1, "业务价值")
        )
        assert score == 80

    def test_business_value_with_cost_reduction(self):
        score, detail = calculate_dimension_score(
            make_app(effectiveness_type="cost_reduction"), make_dimension(1, "业务价值")
        )
        assert score == 70

    def test_tech_innovation_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(difficulty="High"), make_dimension(1, "技术创新性")
        )
        assert score == 100

    def test_user_growth_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(), make_dimension(1, "用户增长性")
        )
        assert score >= 0

    def test_data_richness_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(), make_dimension(1, "数据丰富性")
        )
        assert score >= 0

    def test_efficiency_gain_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(effectiveness_type="efficiency_gain"), make_dimension(1, "增效表现")
        )
        assert score >= 0

    def test_search_volume_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(), make_dimension(1, "搜索热度")
        )
        assert score >= 0

    def test_sharing_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(), make_dimension(1, "分享传播力")
        )
        assert score >= 0

    def test_favorite_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(), make_dimension(1, "收藏关注度")
        )
        assert score >= 0

    def test_default_for_unknown_dimension(self):
        score, detail = calculate_dimension_score(
            make_app(), make_dimension(1, "不存在的维度")
        )
        assert score == 50
        assert "默认评分" in detail

    def test_offline_app_penalty(self):
        online = calculate_dimension_score(
            make_app(status="available"), make_dimension(1, "稳定性和安全性")
        )
        offline = calculate_dimension_score(
            make_app(status="offline"), make_dimension(1, "稳定性和安全性")
        )
        assert offline[0] < online[0]

    def test_beta_app_bonus(self):
        normal = calculate_dimension_score(
            make_app(status="available"), make_dimension(1, "技术创新性")
        )
        beta_result = calculate_dimension_score(
            make_app(status="beta"), make_dimension(1, "技术创新性")
        )
        # beta 应用有技术创新加分
        assert beta_result[0] > 0


# ---------------------------------------------------------------------------
# calculate_three_layer_score
# ---------------------------------------------------------------------------

class TestCalculateThreeLayerScore:
    def test_clamps_to_zero(self):
        dim_map = {1: make_dimension(1, "用户满意度")}
        score = calculate_three_layer_score(
            make_app(monthly_calls=12.5, effectiveness_type="efficiency_gain"),
            config_dimensions=[{"dim_id": 1, "weight": 1.0}],
            dimension_map=dim_map,
            weight_factor=-2.0,
        )
        assert score == 0

    def test_clamps_to_thousand(self):
        dim_map = {1: make_dimension(1, "用户满意度"), 2: make_dimension(2, "业务价值"), 3: make_dimension(3, "技术创新性")}
        score = calculate_three_layer_score(
            make_app(monthly_calls=50, effectiveness_type="revenue_growth", difficulty="High"),
            config_dimensions=[
                {"dim_id": 1, "weight": 1.0},
                {"dim_id": 2, "weight": 1.0},
                {"dim_id": 3, "weight": 1.0},
            ],
            dimension_map=dim_map,
            weight_factor=5.0,
        )
        assert score == 1000

    def test_empty_config_dimensions(self):
        score = calculate_three_layer_score(
            make_app(), config_dimensions=[], dimension_map={}, weight_factor=1.0
        )
        assert score == 0

    def test_missing_dimension_in_map(self):
        score = calculate_three_layer_score(
            make_app(monthly_calls=10),
            config_dimensions=[{"dim_id": 999, "weight": 1.0}],
            dimension_map={},
            weight_factor=1.0,
        )
        assert score == 0

    def test_weight_factor_normalization(self):
        dim_map = {1: make_dimension(1, "用户满意度")}
        score_default = calculate_three_layer_score(
            make_app(monthly_calls=10),
            config_dimensions=[{"dim_id": 1, "weight": 1.0}],
            dimension_map=dim_map,
            weight_factor=1.0,
        )
        score_double = calculate_three_layer_score(
            make_app(monthly_calls=10),
            config_dimensions=[{"dim_id": 1, "weight": 2.0}],
            dimension_map=dim_map,
            weight_factor=1.0,
        )
        assert score_double == score_default * 2


# ---------------------------------------------------------------------------
# calculate_app_score (deprecated)
# ---------------------------------------------------------------------------

class TestCalculateAppScore:
    def test_no_dimensions_uses_monthly_calls(self):
        app = make_app(monthly_calls=10)
        score = calculate_app_score(app, [])
        assert score == 100  # 10 * 10 = 100

    def test_clamps_to_zero(self):
        app = make_app(monthly_calls=-10)
        score = calculate_app_score(app, [])
        assert score == 0

    def test_clamps_to_thousand(self):
        app = make_app(monthly_calls=200)
        score = calculate_app_score(app, [])
        assert score == 1000

    def test_with_dimensions_uses_dimension_scoring(self):
        app = make_app(monthly_calls=15, effectiveness_type="revenue_growth")
        dims = [make_dimension(1, "用户满意度"), make_dimension(2, "业务价值")]
        score = calculate_app_score(app, dims)
        assert score > 0


# ---------------------------------------------------------------------------
# serialize_setting_snapshot
# ---------------------------------------------------------------------------

class TestSerializeSettingSnapshot:
    def test_none_input(self):
        result = serialize_setting_snapshot(None)
        assert result == {}

    def test_setting_with_fields(self):
        setting = SimpleNamespace(
            id=1, app_id=100,
            is_enabled=True, weight_factor=2.0, custom_tags="tag1,tag2",
            ranking_config_id="excellent",
        )
        result = serialize_setting_snapshot(setting)
        assert result["ranking_config_id"] == "excellent"
        assert result["is_enabled"] is True
        assert result["weight_factor"] == 2.0
        assert result["custom_tags"] == "tag1,tag2"
        assert result["id"] == 1
        assert result["app_id"] == 100


# ---------------------------------------------------------------------------
# collect_config_dimension_ids
# ---------------------------------------------------------------------------

class TestCollectConfigDimensionIds:
    def test_with_dimensions_returns_set(self):
        dim1 = SimpleNamespace(dimension_id=1, weight=1.0)
        dim2 = SimpleNamespace(dimension_id=2, weight=0.5)
        config = SimpleNamespace(dimensions=[dim1, dim2])
        result = collect_config_dimension_ids(config)
        assert result == {1, 2}

    def test_empty_dimensions_returns_empty_set(self):
        config = SimpleNamespace(dimensions=[])
        result = collect_config_dimension_ids(config)
        assert result == set()

    def test_none_dimensions_returns_empty_set(self):
        config = SimpleNamespace(dimensions=None)
        result = collect_config_dimension_ids(config)
        assert result == set()


# ---------------------------------------------------------------------------
# validate_publish_preconditions
# ---------------------------------------------------------------------------

class TestValidatePublishPreconditions:
    def test_no_active_configs_raises(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        with pytest.raises(HTTPException, match="无可发布榜单"):
            validate_publish_preconditions(db)
