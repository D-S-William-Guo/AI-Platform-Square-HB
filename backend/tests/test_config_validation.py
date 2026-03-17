import pytest

from app.config import Settings, validate_settings


def test_validate_settings_allows_default_token_in_development():
    settings = Settings(environment="development", admin_token="admin-secret-token")
    validate_settings(settings)


def test_validate_settings_rejects_default_token_in_production():
    settings = Settings(environment="production", admin_token="admin-secret-token")
    with pytest.raises(ValueError, match="ADMIN_TOKEN must be set to a non-default value"):
        validate_settings(settings)


def test_validate_settings_rejects_default_user_password_in_production():
    settings = Settings(
        environment="production",
        admin_token="prod-token",
        user_default_password="ChangeMe_User_123!",
        admin_default_password="safe-admin-password",
    )
    with pytest.raises(ValueError, match="USER_DEFAULT_PASSWORD must be changed in production"):
        validate_settings(settings)


def test_validate_settings_rejects_default_admin_password_in_production():
    settings = Settings(
        environment="production",
        admin_token="prod-token",
        user_default_password="safe-user-password",
        admin_default_password="ChangeMe_Admin_123!",
    )
    with pytest.raises(ValueError, match="ADMIN_DEFAULT_PASSWORD must be changed in production"):
        validate_settings(settings)
