from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.enums import DocumentStatus
from models.base import Base

if TYPE_CHECKING:
    from models.document_chunks import DocumentChunk
    from models.organizations import Organization
    from models.users import User


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            name="fk_documents_organization_id_organizations",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    uploaded_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_documents_uploaded_by_user_id_users",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    storage_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(
            DocumentStatus,
            name="document_status",
            native_enum=False,
            create_constraint=False,
            length=20,
        ),
        default=DocumentStatus.PENDING,
        server_default=DocumentStatus.PENDING.value,
        nullable=False,
    )
    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
        back_populates="documents",
        lazy="raise",
    )
    uploaded_by_user: Mapped[User] = relationship(
        back_populates="uploaded_documents",
        lazy="raise",
    )
    chunks: Mapped[list[DocumentChunk]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            (
                "original_filename = btrim(original_filename) "
                "AND char_length(original_filename) BETWEEN 1 AND 255"
            ),
            name="ck_documents_original_filename_valid",
        ),
        CheckConstraint(
            (
                "content_type = lower(btrim(content_type)) "
                "AND char_length(content_type) BETWEEN 1 AND 255"
            ),
            name="ck_documents_content_type_valid",
        ),
        CheckConstraint(
            (
                "storage_key = btrim(storage_key) "
                "AND char_length(storage_key) BETWEEN 1 AND 512"
            ),
            name="ck_documents_storage_key_valid",
        ),
        CheckConstraint(
            "size_bytes IS NULL OR size_bytes >= 0",
            name="ck_documents_size_bytes_valid",
        ),
        CheckConstraint(
            (
                "sha256 IS NULL OR "
                "sha256 ~ '^[0-9a-f]{64}$'"
            ),
            name="ck_documents_sha256_valid",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')",
            name="ck_documents_status_valid",
        ),
        CheckConstraint(
            (
                "error_message IS NULL OR "
                "(error_message = btrim(error_message) "
                "AND char_length(error_message) BETWEEN 1 AND 1000)"
            ),
            name="ck_documents_error_message_valid",
        ),
        UniqueConstraint(
            "storage_key",
            name="uq_documents_storage_key",
        ),
        Index(
            "ix_documents_organization_created_at_id",
            "organization_id",
            "created_at",
            "id",
        ),
        Index(
            "ix_documents_status_processing_started_at",
            "status",
            "processing_started_at",
        ),
    )
