from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import User


async def get_active_by_id(
    session: AsyncSession,
    user_id: UUID,
) -> User | None:
    statement = select(User).where(
        User.id == user_id,
        User.deleted_at.is_(None),
    )

    return await session.scalar(statement)


async def get_active_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    statement = select(User).where(
        func.lower(User.email) == email.lower(),
        User.deleted_at.is_(None),
    )

    return await session.scalar(statement)


async def list_active(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
) -> list[User]:
    statement = (
        select(User)
        .where(User.deleted_at.is_(None))
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    )

    users = await session.scalars(statement)

    return list(users)