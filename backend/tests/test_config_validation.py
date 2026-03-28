import pytest
from pydantic import ValidationError

from app.config import Settings, validate_settings

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
