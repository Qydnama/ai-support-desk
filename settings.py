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
    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_secure: bool = False
    refresh_token_expire_days: int = Field(
        default=30,
        ge=1,
        le=90,
    )


settings = Settings()