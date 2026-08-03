from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import MessageSenderType
from models.base import Base

if TYPE_CHECKING:
    from models.contacts import Contact
    from models.conversations import Conversation
    from models.users import User


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "conversations.id",
            name="fk_messages_conversation_id_conversations",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    author_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_messages_author_user_id_users",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    author_contact_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "contacts.id",
            name="fk_messages_author_contact_id_contacts",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    sender_type: Mapped[MessageSenderType] = mapped_column(
        Enum(
            MessageSenderType,
            name="message_sender_type",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    conversation: Mapped[Conversation] = relationship(
        back_populates="messages",
        lazy="raise",
    )
    author_user: Mapped[User | None] = relationship(
        back_populates="authored_messages",
        foreign_keys=[author_user_id],
        lazy="raise",
    )
    author_contact: Mapped[Contact | None] = relationship(
        back_populates="authored_messages",
        foreign_keys=[author_contact_id],
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            (
                "content = btrim(content) "
                "AND char_length(content) BETWEEN 1 AND 10000"
            ),
            name="ck_messages_content_valid",
        ),
        CheckConstraint(
            "sender_type IN ('CONTACT', 'AGENT', 'AI', 'SYSTEM')",
            name="ck_messages_sender_type_valid",
        ),
        CheckConstraint(
            (
                "(sender_type = 'CONTACT' "
                "AND author_contact_id IS NOT NULL "
                "AND author_user_id IS NULL) "
                "OR (sender_type = 'AGENT' "
                "AND author_user_id IS NOT NULL "
                "AND author_contact_id IS NULL) "
                "OR (sender_type IN ('AI', 'SYSTEM') "
                "AND author_user_id IS NULL "
                "AND author_contact_id IS NULL)"
            ),
            name="ck_messages_sender_author_valid",
        ),
        Index(
            "ix_messages_conversation_created_at_id",
            "conversation_id",
            "created_at",
            "id",
        ),
    )
