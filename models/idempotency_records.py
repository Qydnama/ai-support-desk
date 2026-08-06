from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.messages import Message


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            name=(
                "fk_idempotency_records_organization_id_organizations"
            ),
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    request_fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "messages.id",
            name="fk_idempotency_records_message_id_messages",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    message: Mapped[Message] = relationship(
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "key ~ '^[A-Za-z0-9._:-]{1,128}$'",
            name="ck_idempotency_records_key_valid",
        ),
        CheckConstraint(
            "request_fingerprint ~ '^[0-9a-f]{64}$'",
            name="ck_idempotency_records_fingerprint_valid",
        ),
        UniqueConstraint(
            "organization_id",
            "key",
            name="uq_idempotency_records_organization_key",
        ),
        UniqueConstraint(
            "message_id",
            name="uq_idempotency_records_message_id",
        ),
    )
