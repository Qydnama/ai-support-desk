from typing import Any

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