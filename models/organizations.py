from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.organization_members import OrganizationMember

class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    memberships: Mapped[list[OrganizationMember]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "name = btrim(name) AND char_length(name) >= 1",
            name="ck_organizations_name_valid",
        ),
        CheckConstraint(
            (
                "slug = lower(slug) "
                "AND slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'"
            ),
            name="ck_organizations_slug_valid",
        ),
        UniqueConstraint(
            "slug",
            name="uq_organizations_slug",
        ),
    )