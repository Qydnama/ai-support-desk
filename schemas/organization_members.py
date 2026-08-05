from uuid import UUID

from pydantic import BaseModel, ConfigDict

from core.enums import OrganizationRole


class OrganizationMemberRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    organization_id: UUID
    user_id: UUID
    role: OrganizationRole


class OrganizationMemberListItem(BaseModel):
    user_id: UUID
    name: str
    role: OrganizationRole
    is_deleted: bool


class OrganizationMemberRoleUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    role: OrganizationRole
