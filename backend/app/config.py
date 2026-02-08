from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI App Square API"
    api_prefix: str = "/api"
    database_url: str = "sqlite:///./ai_app_square.db"
    oa_rule_base_url: str = "https://oa.example.internal"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
