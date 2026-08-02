from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.organization_members import OrganizationMember


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization_memberships: Mapped[list[OrganizationMember]] = relationship(
        back_populates="user",
        passive_deletes="all",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "name = btrim(name) AND char_length(name) >= 1",
            name="ck_users_name_valid",
        ),
        Index(
            "uq_users_email_ci",
            func.lower(email),
            unique=True,
        ),
    )
