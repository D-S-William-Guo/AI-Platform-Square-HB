from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


    static_dir: str = "static"
    upload_dir: str = "static/uploads"
    image_dir: str = "static/images"


def resolve_runtime_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()
from pathlib import Path

from pydantic_settings import BaseSettings


BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "AI App Square API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./ai_app_square.db"
    oa_rule_base_url: str = "https://oa.example.internal"
    static_dir: str = "static"
    upload_dir: str = "static/uploads"
    image_dir: str = "static/images"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


def resolve_runtime_path(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return (BACKEND_DIR / path).resolve()
