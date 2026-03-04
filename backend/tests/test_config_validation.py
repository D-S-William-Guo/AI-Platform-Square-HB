import pytest

from app.config import Settings, validate_settings


def test_validate_settings_allows_default_token_in_development():
    settings = Settings(environment="development", admin_token="admin-secret-token")
    validate_settings(settings)


def test_validate_settings_rejects_default_token_in_production():
    settings = Settings(environment="production", admin_token="admin-secret-token")
    with pytest.raises(ValueError, match="ADMIN_TOKEN must be set to a non-default value"):
        validate_settings(settings)
