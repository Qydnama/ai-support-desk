from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import ConversationStatus
from models.base import Base

if TYPE_CHECKING:
    from models.contacts import Contact
    from models.messages import Message
    from models.organizations import Organization
    from models.users import User


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            name="fk_conversations_organization_id_organizations",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    contact_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "contacts.id",
            name="fk_conversations_contact_id_contacts",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    assigned_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_conversations_assigned_user_id_users",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(
            ConversationStatus,
            name="conversation_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        default=ConversationStatus.OPEN,
        server_default=ConversationStatus.OPEN.value,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    organization: Mapped[Organization] = relationship(
        back_populates="conversations",
        lazy="raise",
    )
    contact: Mapped[Contact] = relationship(
        back_populates="conversations",
        lazy="raise",
    )
    assigned_user: Mapped[User | None] = relationship(
        back_populates="assigned_conversations",
        foreign_keys=[assigned_user_id],
        lazy="raise",
    )
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            (
                "subject = btrim(subject) "
                "AND char_length(subject) BETWEEN 1 AND 200"
            ),
            name="ck_conversations_subject_valid",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'PENDING', 'RESOLVED')",
            name="ck_conversations_status_valid",
        ),
        Index(
            "ix_conversations_organization_created_at_id",
            "organization_id",
            "created_at",
            "id",
        ),
    )
