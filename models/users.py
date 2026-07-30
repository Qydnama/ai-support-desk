from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


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