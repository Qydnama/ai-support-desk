from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    database_url: str

    jwt_secret: SecretStr = Field(
        min_length=32,
    )
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(
        default=15,
        ge=1,
        le=60,
    )
    refresh_cookie_name: str
    refresh_cookie_secure: bool
    refresh_token_expire_days: int = Field(
        default=30,
        ge=1,
        le=90,
    )
    redis_url: str
    redis_test_url: str
    login_rate_limit_max_attempts: int = Field(
        default=5,
        ge=1,
        le=100,
    )
    login_rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        le=3_600,
    )
    login_ip_rate_limit_max_attempts: int = Field(
        default=30,
        ge=1,
        le=1_000,
    )
    login_ip_rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        le=3_600,
    )


settings = Settings()
