from typing import Annotated
from uuid import UUID

from fastapi import Depends

from core.exceptions import ContactNotFoundError
from dependencies.database import SessionDep
from models.contacts import Contact
from repositories import contacts as contact_repository


async def get_existing_contact(
    organization_id: UUID,
    contact_id: UUID,
    session: SessionDep,
) -> Contact:
    contact = await contact_repository.get_active_by_id(
        session=session,
        contact_id=contact_id,
        organization_id=organization_id,
    )

    if contact is None:
        raise ContactNotFoundError()

    return contact


ExistingContactDep = Annotated[
    Contact,
    Depends(get_existing_contact),
]
