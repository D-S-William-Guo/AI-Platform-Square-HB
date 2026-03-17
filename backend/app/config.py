from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "AI App Square API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./ai_app_square.db"
    oa_rule_base_url: str = "https://oa.example.internal"
    static_dir: str = "static"
    upload_dir: str = "static/uploads"
    image_dir: str = "static/images"
    environment: str = "development"
    admin_token: str = "admin-secret-token"
    auth_cookie_name: str = "AI_APP_AUTH"
    auth_session_ttl_hours: int = 12
    user_default_password: str = "ChangeMe_User_123!"
    admin_default_password: str = "ChangeMe_Admin_123!"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def validate_settings(settings_obj: Settings) -> None:
    if settings_obj.environment.lower() in {"prod", "production"} and settings_obj.admin_token == "admin-secret-token":
        raise ValueError("ADMIN_TOKEN must be set to a non-default value in production")
    if settings_obj.environment.lower() in {"prod", "production"}:
        if settings_obj.user_default_password == "ChangeMe_User_123!":
            raise ValueError("USER_DEFAULT_PASSWORD must be changed in production")
        if settings_obj.admin_default_password == "ChangeMe_Admin_123!":
            raise ValueError("ADMIN_DEFAULT_PASSWORD must be changed in production")


settings = Settings()
validate_settings(settings)


def resolve_runtime_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()
