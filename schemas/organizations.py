from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

ORGANIZATION_SLUG_PATTERN = (
    r"^[a-z0-9]+(-[a-z0-9]+)*$"
)


class OrganizationBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(
        min_length=1,
        max_length=100,
    )
    slug: str = Field(
        min_length=1,
        max_length=100,
        pattern=ORGANIZATION_SLUG_PATTERN,
    )


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=ORGANIZATION_SLUG_PATTERN,
    )

    @field_validator("name", "slug")
    @classmethod
    def reject_null(
        cls,
        value: str | None,
    ) -> str:
        if value is None:
            raise ValueError(
                "Field cannot be null; omit it instead",
            )

        return value


class OrganizationRead(OrganizationBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID


class OrganizationSummaryRead(OrganizationRead):
    member_count: int


class OrganizationFilters(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        pattern=ORGANIZATION_SLUG_PATTERN,
    )
    member_user_id: UUID | None = Field(
        default=None,
    )
    min_members: int | None = Field(
        default=None,
        ge=0,
    )
