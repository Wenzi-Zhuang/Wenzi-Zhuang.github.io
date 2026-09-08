from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "production"
    course_code: str = "financial_accounting"
    course_name: str = "会计学"
    course_root: Path = Path("/volume1/courses/financial_accounting")
    database_url: str
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    course_access_password_hash: str
    device_token_secret: str
    frontend_origin: str
    public_api_base: str
    device_token_days: int = 180
    max_upload_mb: int = 50

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

