from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.contacts import Contact


async def get_active_by_id(
    session: AsyncSession,
    *,
    contact_id: UUID,
    organization_id: UUID | None = None,
) -> Contact | None:
    statement = select(Contact).where(
        Contact.id == contact_id,
        Contact.deleted_at.is_(None),
    )

    if organization_id is not None:
        statement = statement.where(
            Contact.organization_id == organization_id,
        )

    return await session.scalar(statement)


async def list_active_by_organization(
    session: AsyncSession,
    *,
    organization_id: UUID,
    limit: int,
    offset: int,
) -> list[Contact]:
    statement = (
        select(Contact)
        .where(
            Contact.organization_id == organization_id,
            Contact.deleted_at.is_(None),
        )
        .order_by(Contact.created_at, Contact.id)
        .offset(offset)
        .limit(limit)
    )

    contacts = await session.scalars(statement)

    return list(contacts)
