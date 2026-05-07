"""Application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RENTAL_CAR_", env_file=".env", extra="ignore")

    service_name: str = "rental-car-api"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    environment: str = Field(default="local", examples=["local", "test", "production"])
    log_level: str = "INFO"
    payment_provider: str = Field(default="wechat_mock", examples=["wechat_mock", "wechat_pay"])


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
