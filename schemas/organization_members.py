from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrganizationMemberRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    organization_id: UUID
    user_id: UUID

class OrganizationMemberListItem(BaseModel):
    user_id: UUID
    name: str
    is_deleted: bool