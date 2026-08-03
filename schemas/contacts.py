from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        min_length=1,
        max_length=100,
    )
    email: EmailStr


class ContactRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    organization_id: UUID
    name: str
    email: EmailStr
    created_at: datetime
