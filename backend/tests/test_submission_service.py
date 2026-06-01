"""Unit tests for submission_service.py."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.services.submission_service import (
    apply_change_request_to_app,
    apply_submission_fields,
    build_submission_update_fields,
    ensure_no_duplicate_active_submission,
    ensure_no_duplicate_province_app,
    normalize_dedupe_text,
    validate_group_app_payload,
    validate_review_reason,
    validate_submission_payload,
)

from helpers import make_submission_payload


# ---------------------------------------------------------------------------
# normalize_dedupe_text
# ---------------------------------------------------------------------------

class TestNormalizeDedupeText:
    def test_trims_and_lowercases(self):
        assert normalize_dedupe_text("  Hello   World  ") == "hello world"

    def test_uppercase_to_lowercase(self):
        assert normalize_dedupe_text("ABC DEF") == "abc def"

    def test_empty_string(self):
        assert normalize_dedupe_text("") == ""

    def test_whitespace_only(self):
        assert normalize_dedupe_text("   ") == ""


# ---------------------------------------------------------------------------
# validate_submission_payload
# ---------------------------------------------------------------------------

class TestValidateSubmissionPayload:
    def test_valid_payload_passes(self):
        payload = make_submission_payload()
        validate_submission_payload(payload)

    def test_invalid_effectiveness_type_raises(self):
        payload = make_submission_payload(effectiveness_type="invalid_type")
        with pytest.raises(HTTPException, match="Invalid effectiveness_type"):
            validate_submission_payload(payload)

    def test_invalid_data_level_raises(self):
        payload = make_submission_payload(data_level="L5")
        with pytest.raises(HTTPException, match="Invalid data_level"):
            validate_submission_payload(payload)

    def test_invalid_category_raises(self):
        payload = make_submission_payload(category="invalid_category")
        with pytest.raises(HTTPException, match="Invalid category"):
            validate_submission_payload(payload)

    def test_invalid_difficulty_raises(self):
        payload = make_submission_payload(difficulty="Impossible")
        with pytest.raises(HTTPException, match="Invalid difficulty"):
            validate_submission_payload(payload)


# ---------------------------------------------------------------------------
# validate_review_reason
# ---------------------------------------------------------------------------

class TestValidateReviewReason:
    def test_valid_reason_returns_stripped(self):
        result = validate_review_reason("  good reason  ")
        assert result == "good reason"

    def test_none_raises(self):
        with pytest.raises(HTTPException, match="拒绝原因不能为空"):
            validate_review_reason(None)

    def test_empty_string_raises(self):
        with pytest.raises(HTTPException, match="拒绝原因不能为空"):
            validate_review_reason("")

    def test_too_short_raises(self):
        with pytest.raises(HTTPException, match="拒绝原因不能为空"):
            validate_review_reason("a")

    def test_minimum_length_passes(self):
        result = validate_review_reason("ab")
        assert result == "ab"

    def test_too_long_raises(self):
        with pytest.raises(HTTPException, match="拒绝原因最多 255 个字符"):
            validate_review_reason("a" * 256)


# ---------------------------------------------------------------------------
# validate_group_app_payload
# ---------------------------------------------------------------------------

class TestValidateGroupAppPayload:
    def test_valid_payload_passes(self):
        payload = make_submission_payload(status="available", access_mode="direct")
        validate_group_app_payload(payload)

    def test_invalid_status_raises(self):
        payload = make_submission_payload(status="unknown")
        with pytest.raises(HTTPException, match="Invalid status"):
            validate_group_app_payload(payload)

    def test_invalid_access_mode_raises(self):
        payload = make_submission_payload(access_mode="magic", status="available")
        with pytest.raises(HTTPException, match="Invalid access_mode"):
            validate_group_app_payload(payload)


# ---------------------------------------------------------------------------
# build_submission_update_fields
# ---------------------------------------------------------------------------

class TestBuildSubmissionUpdateFields:
    def test_includes_company_and_department(self):
        payload = make_submission_payload()
        result = build_submission_update_fields(payload, company="TestCo", department="Eng")
        assert result["company"] == "TestCo"
        assert result["department"] == "Eng"
        assert result["unit_name"] == "TestCo"

    def test_ranking_fields_are_disabled_by_default(self):
        payload = make_submission_payload()
        result = build_submission_update_fields(payload, company="TestCo", department="Eng")
        assert result["ranking_enabled"] is False
        assert result["ranking_weight"] == 1.0
        assert result["ranking_tags"] == ""
        assert result["ranking_dimensions"] == ""

    def test_validates_payload_internally(self):
        payload = make_submission_payload(effectiveness_type="bad")
        with pytest.raises(HTTPException):
            build_submission_update_fields(payload, company="TestCo", department="Eng")


# ---------------------------------------------------------------------------
# apply_submission_fields
# ---------------------------------------------------------------------------

class TestApplySubmissionFields:
    def test_applies_only_existing_attributes(self):
        obj = SimpleNamespace(name="old", age=10)
        fields = {"name": "new", "age": 20, "nonexistent": "ignored"}
        apply_submission_fields(obj, fields)
        assert obj.name == "new"
        assert obj.age == 20
        assert not hasattr(obj, "nonexistent")

    def test_empty_fields_does_nothing(self):
        obj = SimpleNamespace(name="unchanged")
        apply_submission_fields(obj, {})
        assert obj.name == "unchanged"


# ---------------------------------------------------------------------------
# apply_change_request_to_app
# ---------------------------------------------------------------------------

class TestApplyChangeRequestToApp:
    def _make_cr(self, **overrides):
        defaults = dict(
            app_name="new-name", unit_name="new-unit",
            company="new-co", department="new-dept",
            category="new-cat", scenario="new scenario",
            monthly_calls=100, difficulty="Low",
            contact="new contact", detail_doc_url="http://doc",
            detail_doc_name="doc.pdf", embedded_system="sys",
            problem_statement="problem", effectiveness_type="cost_reduction",
            effectiveness_metric="metric", cover_image_url="http://img",
        )
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def test_maps_all_fields(self):
        app = SimpleNamespace()
        cr = self._make_cr()
        apply_change_request_to_app(app, cr)
        assert app.name == "new-name"
        assert app.org == "new-unit"
        assert app.company == "new-co"
        assert app.category == "new-cat"
        assert app.description == "new scenario"
        assert app.monthly_calls == 100

    def test_none_monthly_calls_defaults_to_zero(self):
        app = SimpleNamespace()
        cr = self._make_cr(monthly_calls=None)
        apply_change_request_to_app(app, cr)
        assert app.monthly_calls == 0.0

    def test_none_difficulty_defaults_to_medium(self):
        app = SimpleNamespace()
        cr = self._make_cr(difficulty=None)
        apply_change_request_to_app(app, cr)
        assert app.difficulty == "Medium"

    def test_none_cover_image_defaults_to_empty(self):
        app = SimpleNamespace()
        cr = self._make_cr(cover_image_url=None)
        apply_change_request_to_app(app, cr)
        assert app.cover_image_url == ""


# ---------------------------------------------------------------------------
# ensure_no_duplicate_active_submission
# ---------------------------------------------------------------------------

class TestEnsureNoDuplicateActiveSubmission:
    def test_no_duplicate_does_not_raise(self):
        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.first.return_value = None
        db.query.return_value = mock_query
        # Should not raise
        ensure_no_duplicate_active_submission(db, app_name="unique", unit_name="unique-co")

    def test_duplicate_raises_409(self):
        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value.filter.return_value = mock_query
        mock_query.first.return_value = SimpleNamespace(id=1)
        db.query.return_value = mock_query
        with pytest.raises(HTTPException, match="请勿重复提交"):
            ensure_no_duplicate_active_submission(db, app_name="dup", unit_name="dup-co")


# ---------------------------------------------------------------------------
# ensure_no_duplicate_province_app
# ---------------------------------------------------------------------------

class TestEnsureNoDuplicateProvinceApp:
    def test_no_duplicate_does_not_raise(self):
        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.first.return_value = None
        db.query.return_value = mock_query
        ensure_no_duplicate_province_app(db, app_name="unique", unit_name="unique-co")

    def test_duplicate_raises_409(self):
        db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value = mock_query
        mock_query.filter.return_value.filter.return_value.filter.return_value = mock_query
        mock_query.first.return_value = SimpleNamespace(id=1)
        db.query.return_value = mock_query
        with pytest.raises(HTTPException, match="不能重复创建"):
            ensure_no_duplicate_province_app(db, app_name="dup", unit_name="dup-co")
