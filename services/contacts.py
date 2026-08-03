from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ContactEmailAlreadyExistsError
from database_errors import is_contact_email_unique_violation
from models.contacts import Contact
from models.organizations import Organization
from schemas.contacts import ContactCreate


async def create_contact(
    session: AsyncSession,
    organization: Organization,
    data: ContactCreate,
) -> Contact:
    contact = Contact(
        id=uuid4(),
        organization_id=organization.id,
        name=data.name,
        email=str(data.email),
    )

    session.add(contact)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_contact_email_unique_violation(exc):
            raise ContactEmailAlreadyExistsError() from exc

        raise
    except Exception:
        await session.rollback()
        raise

    return contact
