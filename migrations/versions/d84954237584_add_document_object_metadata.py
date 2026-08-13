"""add document object metadata

Revision ID: d84954237584
Revises: 6e8d6c0665cd
Create Date: 2026-08-12 15:12:22.802666

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd84954237584'
down_revision: Union[str, Sequence[str], None] = '6e8d6c0665cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "documents",
        sa.Column(
            "size_bytes",
            sa.BigInteger(),
            nullable=True,
        ),
    )
    op.add_column(
        "documents",
        sa.Column(
            "sha256",
            sa.String(length=64),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_documents_size_bytes_valid",
        "documents",
        "size_bytes IS NULL OR size_bytes >= 0",
    )
    op.create_check_constraint(
        "ck_documents_sha256_valid",
        "documents",
        "sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$'",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_documents_sha256_valid",
        "documents",
        type_="check",
    )
    op.drop_constraint(
        "ck_documents_size_bytes_valid",
        "documents",
        type_="check",
    )
    op.drop_column("documents", "sha256")
    op.drop_column("documents", "size_bytes")
