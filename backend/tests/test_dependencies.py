"""Unit tests for dependencies.py — helpers, pagination, audit, auth."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.dependencies import (
    build_audit_payload_summary,
    extract_bearer_token,
    paginate_query,
    ranking_audit_actor,
    to_public_user,
)


# ---------------------------------------------------------------------------
# extract_bearer_token
# ---------------------------------------------------------------------------

class TestExtractBearerToken:
    def test_none_returns_none(self):
        assert extract_bearer_token(None) is None

    def test_bearer_prefix_returns_token(self):
        assert extract_bearer_token("Bearer abc123") == "abc123"

    def test_case_insensitive(self):
        assert extract_bearer_token("bearer abc") == "abc"

    def test_no_bearer_prefix_returns_none(self):
        assert extract_bearer_token("NotBearer xyz") is None

    def test_bearer_without_token_returns_none(self):
        assert extract_bearer_token("Bearer ") is None

    def test_empty_string_returns_none(self):
        assert extract_bearer_token("") is None

    def test_bearer_with_extra_spaces(self):
        assert extract_bearer_token("Bearer  token123 ") == "token123"


# ---------------------------------------------------------------------------
# to_public_user
# ---------------------------------------------------------------------------

class TestToPublicUser:
    def test_full_user(self):
        user = SimpleNamespace(
            id=1, username="testuser", chinese_name="测试", email="test@test.com",
            phone="13800138000", role="user", company="TestCo", department="Eng",
            is_active=True, can_submit=True, must_change_password=False,
        )
        result = to_public_user(user)
        # to_public_user returns UserPublic (Pydantic model)
        assert result.username == "testuser"
        assert result.role == "user"

    def test_none_fields_default_to_empty_string(self):
        user = SimpleNamespace(
            id=1, username="u", chinese_name="", email="",
            phone="", role="user", company="", department="",
            is_active=True, can_submit=True, must_change_password=False,
        )
        result = to_public_user(user)
        assert result.chinese_name == ""
        assert result.email == ""
        assert result.phone == ""
        assert result.company == ""


# ---------------------------------------------------------------------------
# build_audit_payload_summary
# ---------------------------------------------------------------------------

class TestBuildAuditPayloadSummary:
    def test_all_params_included(self):
        summary = build_audit_payload_summary(
            intent="submit", result="success", context="test",
            user_role="admin",
        )
        data = json.loads(summary)
        assert data["intent"] == "submit"
        assert data["result"] == "success"
        assert data["context"] == "test"
        assert data["user_role"] == "admin"

    def test_defaults_to_empty_strings(self):
        summary = build_audit_payload_summary()
        data = json.loads(summary)
        assert data["intent"] == ""
        assert data["result"] == ""
        assert data["context"] == ""


# ---------------------------------------------------------------------------
# paginate_query
# ---------------------------------------------------------------------------

class TestPaginateQuery:
    def test_empty_result(self):
        query = MagicMock()
        query.order_by.return_value.count.return_value = 0
        result = paginate_query(query, page=1, page_size=10)
        assert result.total == 0
        assert result.total_pages == 0
        assert result.items == []

    def test_single_page(self):
        items = [SimpleNamespace(id=i) for i in range(5)]
        query = MagicMock()
        query.order_by.return_value.count.return_value = 5
        query.offset.return_value.limit.return_value.all.return_value = items
        result = paginate_query(query, page=1, page_size=10)
        assert result.total == 5
        assert result.total_pages == 1
        assert len(result.items) == 5

    def test_multi_page(self):
        query = MagicMock()
        query.order_by.return_value.count.return_value = 25
        query.offset.return_value.limit.return_value.all.return_value = [
            SimpleNamespace(id=i) for i in range(10)
        ]
        result = paginate_query(query, page=2, page_size=10)
        assert result.total == 25
        assert result.total_pages == 3
        assert result.page == 2

    def test_last_page_clamped(self):
        query = MagicMock()
        query.order_by.return_value.count.return_value = 20
        query.offset.return_value.limit.return_value.all.return_value = [
            SimpleNamespace(id=i) for i in range(20)
        ]
        result = paginate_query(query, page=99, page_size=10)
        assert result.total == 20
        assert result.total_pages == 2


# ---------------------------------------------------------------------------
# ranking_audit_actor
# ---------------------------------------------------------------------------

class TestRankingAuditActor:
    def test_user_returns_username(self):
        user = SimpleNamespace(username="admin_user")
        assert ranking_audit_actor(user) == "admin_user"

    def test_none_returns_system(self):
        assert ranking_audit_actor(None) == "system"
