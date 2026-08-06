import asyncio
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database_errors import is_contact_email_unique_violation
from models.contacts import Contact


def create_organization(
    client: TestClient,
    suffix: str,
) -> tuple[dict[str, str], dict[str, str]]:
    email = f"owner-{suffix}@example.com"
    password = "correct-horse-battery-staple"
    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Owner {suffix}",
            "email": email,
            "password": password,
        },
    )
    assert register_response.status_code == 201
    login_response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_response.status_code == 200

    headers = {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        ),
    }
    response = client.post(
        "/organizations",
        headers=headers,
        json={
            "name": f"Organization {suffix}",
            "slug": f"contacts-{suffix}",
        },
    )
    assert response.status_code == 201
    return response.json(), headers


def test_contact_create_get_and_list(
    client: TestClient,
) -> None:
    organization, headers = create_organization(client, "lifecycle")
    path = f"/organizations/{organization['id']}/contacts"

    create_response = client.post(
        path,
        headers=headers,
        json={
            "name": "Alice Customer",
            "email": "alice@example.com",
        },
    )
    assert create_response.status_code == 201
    contact = create_response.json()
    assert contact["organization_id"] == organization["id"]
    assert create_response.headers["location"] == (
        f"{path}/{contact['id']}"
    )

    get_response = client.get(
        f"{path}/{contact['id']}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json() == contact

    list_response = client.get(path, headers=headers)
    assert list_response.status_code == 200
    assert list_response.json() == [contact]


def test_contact_email_is_unique_inside_organization(
    client: TestClient,
) -> None:
    first_organization, first_headers = create_organization(
        client,
        "unique-a",
    )
    second_organization, second_headers = create_organization(
        client,
        "unique-b",
    )

    for organization, headers, email in (
        (first_organization, first_headers, "customer@example.com"),
        (second_organization, second_headers, "CUSTOMER@example.com"),
    ):
        response = client.post(
            f"/organizations/{organization['id']}/contacts",
            headers=headers,
            json={"name": "Customer", "email": email},
        )
        assert response.status_code == 201

    duplicate = client.post(
        f"/organizations/{first_organization['id']}/contacts",
        headers=first_headers,
        json={"name": "Duplicate", "email": "CUSTOMER@example.com"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "contact_email_already_exists"


def test_contact_not_found(
    client: TestClient,
) -> None:
    organization, headers = create_organization(client, "missing")
    response = client.get(
        f"/organizations/{organization['id']}/contacts/{uuid4()}",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["code"] == "contact_not_found"


def test_contacts_require_tenant_membership(
    client: TestClient,
) -> None:
    organization, owner_headers = create_organization(
        client,
        "protected-a",
    )
    _, outsider_headers = create_organization(
        client,
        "protected-b",
    )
    path = f"/organizations/{organization['id']}/contacts"
    contact_response = client.post(
        path,
        headers=owner_headers,
        json={
            "name": "Protected customer",
            "email": "protected@example.com",
        },
    )
    assert contact_response.status_code == 201
    contact_id = contact_response.json()["id"]

    assert client.get(path).status_code == 401
    assert client.get(
        f"{path}/{contact_id}",
        headers=outsider_headers,
    ).status_code == 403
    assert client.post(
        path,
        headers=outsider_headers,
        json={
            "name": "Intruder",
            "email": "intruder@example.com",
        },
    ).status_code == 403


def test_unique_index_arbitrates_concurrent_contact_creation(
    client: TestClient,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization, _headers = create_organization(
        client,
        "concurrent-unique",
    )
    organization_id = UUID(organization["id"])

    async def create_concurrent_duplicates() -> tuple[list[str], int]:
        both_prechecks_finished = asyncio.Barrier(2)

        async def create_contact_with_precheck(
            *,
            name: str,
            email: str,
        ) -> str:
            async with concurrent_session_factory() as session:
                existing_contact_id = await session.scalar(
                    select(Contact.id).where(
                        Contact.organization_id == organization_id,
                        func.lower(Contact.email) == email.lower(),
                    ),
                )
                assert existing_contact_id is None

                await both_prechecks_finished.wait()

                session.add(
                    Contact(
                        id=uuid4(),
                        organization_id=organization_id,
                        name=name,
                        email=email,
                    ),
                )

                try:
                    await session.commit()
                except IntegrityError as exc:
                    await session.rollback()
                    assert is_contact_email_unique_violation(exc)
                    return "conflict"

            return "committed"

        results = await asyncio.gather(
            create_contact_with_precheck(
                name="First duplicate",
                email="duplicate@example.com",
            ),
            create_contact_with_precheck(
                name="Second duplicate",
                email="DUPLICATE@example.com",
            ),
        )

        async with concurrent_session_factory() as verification_session:
            stored_count = await verification_session.scalar(
                select(func.count())
                .select_from(Contact)
                .where(
                    Contact.organization_id == organization_id,
                    func.lower(Contact.email)
                    == "duplicate@example.com",
                ),
            )

        assert stored_count is not None

        return results, stored_count

    results, stored_count = asyncio.run(
        create_concurrent_duplicates(),
    )

    assert sorted(results) == ["committed", "conflict"]
    assert stored_count == 1
