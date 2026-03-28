from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]
MYSQL_URL_PREFIX = "mysql+pymysql://"
PRODUCTION_ENVIRONMENTS = {"prod", "production"}


class Settings(BaseSettings):
    app_name: str = "AI App Square API"
    api_prefix: str = "/api"
    database_url: str
    test_database_url: str | None = None
    app_host: str = "0.0.0.0"
    app_port: int = 80
    backend_dev_port: int = 8000
    frontend_dev_port: int = 5173
    oa_rule_base_url: str = "https://oa.example.internal"
    static_dir: str = "static"
    upload_dir: str = "static/uploads"
    image_dir: str = "static/images"
    environment: str = "development"
    auth_provider_mode: str = "local"
    auth_cookie_name: str = "AI_APP_AUTH"
    auth_session_ttl_hours: int = 12
    oa_sso_login_url: str = ""
    external_sso_login_url: str = ""
    allowed_origins: str = ""
    allowed_hosts: str = ""
    enable_api_docs: bool | None = None
    user_default_password: str = "ChangeMe_User_123!"
    admin_default_password: str = "ChangeMe_Admin_123!"
    user_sync_token: str = ""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


def validate_settings(settings_obj: Settings) -> None:
    for name, value in (
        ("APP_PORT", settings_obj.app_port),
        ("BACKEND_DEV_PORT", settings_obj.backend_dev_port),
        ("FRONTEND_DEV_PORT", settings_obj.frontend_dev_port),
    ):
        if value < 1 or value > 65535:
            raise ValueError(f"{name} must be between 1 and 65535")
    if not settings_obj.database_url:
        raise ValueError("DATABASE_URL must be set")
    if not settings_obj.database_url.startswith(MYSQL_URL_PREFIX):
        raise ValueError("DATABASE_URL must use the mysql+pymysql:// scheme")
    if settings_obj.test_database_url and not settings_obj.test_database_url.startswith(MYSQL_URL_PREFIX):
        raise ValueError("TEST_DATABASE_URL must use the mysql+pymysql:// scheme")
    if settings_obj.auth_provider_mode not in {"local", "oa", "external_sso"}:
        raise ValueError("AUTH_PROVIDER_MODE must be one of: local, oa, external_sso")
    if is_production_environment(settings_obj):
        if settings_obj.user_default_password == "ChangeMe_User_123!":
            raise ValueError("USER_DEFAULT_PASSWORD must be changed in production")
        if settings_obj.admin_default_password == "ChangeMe_Admin_123!":
            raise ValueError("ADMIN_DEFAULT_PASSWORD must be changed in production")

def resolve_runtime_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()


def is_production_environment(settings_obj: Settings) -> bool:
    return settings_obj.environment.lower() in PRODUCTION_ENVIRONMENTS


def is_development_environment(settings_obj: Settings) -> bool:
    return not is_production_environment(settings_obj)


def parse_csv_setting(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def get_allowed_origins(settings_obj: Settings) -> list[str]:
    configured = parse_csv_setting(settings_obj.allowed_origins)
    if configured:
        return configured
    if is_production_environment(settings_obj):
        return []
    frontend_port = settings_obj.frontend_dev_port
    return [
        f"http://127.0.0.1:{frontend_port}",
        f"http://localhost:{frontend_port}",
    ]


def get_allowed_hosts(settings_obj: Settings) -> list[str]:
    configured = parse_csv_setting(settings_obj.allowed_hosts)
    if configured:
        return configured
    hosts = ["127.0.0.1", "localhost", "testserver"]
    if settings_obj.app_host not in {"0.0.0.0", "::", ""}:
        hosts.append(settings_obj.app_host)
    return hosts


def is_api_docs_enabled(settings_obj: Settings) -> bool:
    if settings_obj.enable_api_docs is not None:
        return settings_obj.enable_api_docs
    return not is_production_environment(settings_obj)


settings = Settings()
validate_settings(settings)
