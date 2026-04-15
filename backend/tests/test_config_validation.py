import pytest
from pydantic import ValidationError

from app.config import (
    Settings,
    get_app_category_options,
    get_allowed_hosts,
    get_allowed_origins,
    is_api_docs_enabled,
    is_auth_cookie_secure,
    validate_settings,
)
from app.identity import get_identity_provider

MYSQL_URL = "mysql+pymysql://tester:secret@127.0.0.1:3306/ai_app_square?charset=utf8mb4"


def test_validate_settings_allows_default_passwords_in_development():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="development",
    )
    validate_settings(settings)


def test_validate_settings_rejects_default_user_password_in_production():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="production",
        user_default_password="ChangeMe_User_123!",
        admin_default_password="safe-admin-password",
    )
    with pytest.raises(ValueError, match="USER_DEFAULT_PASSWORD must be changed in production"):
        validate_settings(settings)


def test_validate_settings_rejects_default_admin_password_in_production():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="production",
        user_default_password="safe-user-password",
        admin_default_password="ChangeMe_Admin_123!",
    )
    with pytest.raises(ValueError, match="ADMIN_DEFAULT_PASSWORD must be changed in production"):
        validate_settings(settings)


def test_settings_require_database_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_validate_settings_rejects_non_mysql_database_url():
    settings = Settings(
        database_url="postgresql://legacy:legacy@127.0.0.1:5432/legacy",
        environment="development",
    )

    with pytest.raises(ValueError, match="mysql\\+pymysql"):
        validate_settings(settings)


def test_validate_settings_rejects_unknown_auth_provider_mode():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="development",
        auth_provider_mode="legacy",
    )

    with pytest.raises(ValueError, match="AUTH_PROVIDER_MODE"):
        validate_settings(settings)


def test_get_app_category_options_from_csv():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="development",
        app_category_options="前端市场类,客户服务类,云网运营类,管理支撑类",
    )

    assert get_app_category_options(settings) == ["前端市场类", "客户服务类", "云网运营类", "管理支撑类"]


def test_get_app_category_options_rejects_duplicates():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="development",
        app_category_options="前端市场类,客户服务类,前端市场类",
    )

    with pytest.raises(ValueError, match="duplicated"):
        get_app_category_options(settings)


def test_get_identity_provider_rejects_unknown_auth_provider_mode():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="development",
    )
    settings.auth_provider_mode = "legacy"

    with pytest.raises(ValueError, match="Unsupported AUTH_PROVIDER_MODE"):
        get_identity_provider(settings)


def test_get_allowed_origins_defaults_to_dev_frontend_hosts():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="development",
        frontend_dev_port=5173,
    )

    assert get_allowed_origins(settings) == [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ]


def test_get_allowed_origins_defaults_to_no_cors_in_production():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="production",
        user_default_password="safe-user-password",
        admin_default_password="safe-admin-password",
    )

    assert get_allowed_origins(settings) == []


def test_get_allowed_hosts_uses_configured_csv():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="development",
        allowed_hosts="ai.example.internal, 10.0.0.10",
    )

    assert get_allowed_hosts(settings) == ["ai.example.internal", "10.0.0.10"]


def test_api_docs_default_to_disabled_in_production():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="production",
        user_default_password="safe-user-password",
        admin_default_password="safe-admin-password",
    )

    assert is_api_docs_enabled(settings) is False


def test_auth_cookie_secure_defaults_to_false_in_development():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="development",
    )

    assert is_auth_cookie_secure(settings) is False


def test_auth_cookie_secure_defaults_to_true_in_production():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="production",
        user_default_password="safe-user-password",
        admin_default_password="safe-admin-password",
    )

    assert is_auth_cookie_secure(settings) is True


def test_auth_cookie_secure_can_be_disabled_explicitly_in_production():
    settings = Settings(
        database_url=MYSQL_URL,
        environment="production",
        user_default_password="safe-user-password",
        admin_default_password="safe-admin-password",
        auth_cookie_secure=False,
    )

    assert is_auth_cookie_secure(settings) is False
