from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import OrganizationRole
from models.base import Base

if TYPE_CHECKING:
    from models.organizations import Organization
    from models.users import User


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            name=("fk_organization_members_organization_id_organizations"),
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_organization_members_user_id_users",
            ondelete="RESTRICT",
        ),
        primary_key=True,
    )
    role: Mapped[OrganizationRole] = mapped_column(
        Enum(
            OrganizationRole,
            name="organization_role",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        default=OrganizationRole.AGENT,
        server_default=OrganizationRole.AGENT.value,
        nullable=False,
    )
    organization: Mapped[Organization] = relationship(
        back_populates="memberships",
        lazy="raise",
    )
    user: Mapped[User] = relationship(
        back_populates="organization_memberships",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('OWNER', 'ADMIN', 'AGENT')",
            name="ck_organization_members_role_valid",
        ),
        Index(
            "ix_organization_members_user_id_organization_id",
            "user_id",
            "organization_id",
        ),
    )
