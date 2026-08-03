from fastapi import APIRouter, Response, status

from dependencies.contacts import ExistingContactDep
from dependencies.database import SessionDep
from dependencies.organizations import ExistingOrganizationDep
from dependencies.pagination import PaginationDep
from repositories import contacts as contact_repository
from schemas.contacts import ContactCreate, ContactRead
from services import contacts as contact_service

router = APIRouter(
    prefix="/organizations/{organization_id}/contacts",
    tags=["contacts"],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="List organization contacts",
)
async def list_contacts(
    existing_organization: ExistingOrganizationDep,
    pagination: PaginationDep,
    session: SessionDep,
) -> list[ContactRead]:
    contacts = await contact_repository.list_active_by_organization(
        session=session,
        organization_id=existing_organization.id,
        limit=pagination.limit,
        offset=pagination.offset,
    )

    return [
        ContactRead.model_validate(contact)
        for contact in contacts
    ]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create an organization contact",
)
async def create_contact(
    data: ContactCreate,
    existing_organization: ExistingOrganizationDep,
    response: Response,
    session: SessionDep,
) -> ContactRead:
    contact = await contact_service.create_contact(
        session=session,
        organization=existing_organization,
        data=data,
    )

    response.headers["Location"] = (
        f"/organizations/{existing_organization.id}/contacts/{contact.id}"
    )

    return ContactRead.model_validate(contact)


@router.get(
    "/{contact_id}",
    status_code=status.HTTP_200_OK,
    summary="Get an organization contact",
)
async def get_contact(
    contact: ExistingContactDep,
) -> ContactRead:
    return ContactRead.model_validate(contact)
