from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.conversations import Conversation
    from models.messages import Message
    from models.organizations import Organization


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            name="fk_contacts_organization_id_organizations",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    organization: Mapped[Organization] = relationship(
        back_populates="contacts",
        lazy="raise",
    )
    conversations: Mapped[list[Conversation]] = relationship(
        back_populates="contact",
        passive_deletes="all",
        lazy="raise",
    )
    authored_messages: Mapped[list[Message]] = relationship(
        back_populates="author_contact",
        passive_deletes="all",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "name = btrim(name) AND char_length(name) >= 1",
            name="ck_contacts_name_valid",
        ),
        Index(
            "uq_contacts_organization_email_ci",
            organization_id,
            func.lower(email),
            unique=True,
        ),
    )
