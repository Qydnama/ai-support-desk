from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.documents import Document


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "organizations.id",
            name=(
                "fk_document_chunks_organization_id_organizations"
            ),
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "documents.id",
            name="fk_document_chunks_document_id_documents",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    page_start: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    page_end: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    index_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped[Document] = relationship(
        back_populates="chunks",
        lazy="raise",
    )

    __table_args__ = (
        CheckConstraint(
            "chunk_index >= 0",
            name="ck_document_chunks_chunk_index_nonnegative",
        ),
        CheckConstraint(
            (
                "content = btrim(content) "
                "AND char_length(content) >= 1"
            ),
            name="ck_document_chunks_content_valid",
        ),
        CheckConstraint(
            "content_hash ~ '^[0-9a-f]{64}$'",
            name="ck_document_chunks_content_hash_valid",
        ),
        CheckConstraint(
            (
                "page_start IS NULL OR page_start >= 1"
            ),
            name="ck_document_chunks_page_start_valid",
        ),
        CheckConstraint(
            (
                "page_end IS NULL OR page_end >= 1"
            ),
            name="ck_document_chunks_page_end_valid",
        ),
        CheckConstraint(
            (
                "(page_start IS NULL AND page_end IS NULL) "
                "OR (page_start IS NOT NULL "
                "AND page_end IS NOT NULL "
                "AND page_start <= page_end)"
            ),
            name="ck_document_chunks_page_range_valid",
        ),
        CheckConstraint(
            (
                "index_version = btrim(index_version) "
                "AND char_length(index_version) BETWEEN 1 AND 64"
            ),
            name="ck_document_chunks_index_version_valid",
        ),
        UniqueConstraint(
            "document_id",
            "chunk_index",
            "index_version",
            name=(
                "uq_document_chunks_document_index_version"
            ),
        ),
        Index(
            "ix_document_chunks_organization_document",
            "organization_id",
            "document_id",
        ),
    )
