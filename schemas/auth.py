from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    name: str = Field(
        min_length=1,
        max_length=100,
    )
    email: EmailStr
    password: SecretStr = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator(
        "name",
        "email",
        mode="before",
    )
    @classmethod
    def strip_non_password_fields(
        cls,
        value: Any,
    ) -> Any:
        if isinstance(value, str):
            return value.strip()

        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    email: EmailStr
    password: SecretStr = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator(
        "email",
        mode="before",
    )
    @classmethod
    def strip_email(
        cls,
        value: Any,
    ) -> Any:
        if isinstance(value, str):
            return value.strip()

        return value


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"