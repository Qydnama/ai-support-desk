import asyncio
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.documents import Document


def create_organization(
    client: TestClient,
    suffix: str,
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    email = f"document-owner-{suffix}@example.com"
    password = "correct-horse-battery-staple"
    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Document owner {suffix}",
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
    organization_response = client.post(
        "/organizations",
        headers=headers,
        json={
            "name": f"Document organization {suffix}",
            "slug": f"documents-{suffix}",
        },
    )
    assert organization_response.status_code == 201

    return (
        organization_response.json(),
        headers,
        register_response.json(),
    )


def create_stored_document(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    organization_id: UUID,
    uploaded_by_user_id: UUID,
) -> UUID:
    async def create() -> UUID:
        document = Document(
            id=uuid4(),
            organization_id=organization_id,
            uploaded_by_user_id=uploaded_by_user_id,
            original_filename="guide.txt",
            content_type="text/plain",
            storage_key=f"documents/{uuid4()}.txt",
        )

        async with session_factory() as session:
            session.add(document)
            await session.commit()

        return document.id

    return asyncio.run(create())


def test_document_get_and_list_are_scoped_to_organization(
    client: TestClient,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    organization, headers, owner = create_organization(
        client,
        "read-lifecycle",
    )
    document_id = create_stored_document(
        concurrent_session_factory,
        organization_id=UUID(organization["id"]),
        uploaded_by_user_id=UUID(owner["id"]),
    )
    path = f"/organizations/{organization['id']}/documents"

    get_response = client.get(
        f"{path}/{document_id}",
        headers=headers,
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == str(document_id)
    assert get_response.json()["organization_id"] == organization["id"]
    assert get_response.json()["status"] == "PENDING"
    assert "storage_key" not in get_response.json()

    list_response = client.get(path, headers=headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [
        str(document_id),
    ]


def test_document_api_rejects_other_tenants_and_wrong_paths(
    client: TestClient,
    concurrent_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first_organization, first_headers, first_owner = create_organization(
        client,
        "tenant-a",
    )
    second_organization, _, second_owner = create_organization(
        client,
        "tenant-b",
    )
    second_document_id = create_stored_document(
        concurrent_session_factory,
        organization_id=UUID(second_organization["id"]),
        uploaded_by_user_id=UUID(second_owner["id"]),
    )
    first_path = (
        f"/organizations/{first_organization['id']}/documents"
    )
    second_path = (
        f"/organizations/{second_organization['id']}/documents"
    )

    assert client.get(first_path).status_code == 401

    foreign_list_response = client.get(
        second_path,
        headers=first_headers,
    )
    assert foreign_list_response.status_code == 403
    assert foreign_list_response.json()["code"] == (
        "organization_member_required"
    )

    wrong_path_response = client.get(
        f"{first_path}/{second_document_id}",
        headers=first_headers,
    )
    assert wrong_path_response.status_code == 404
    assert wrong_path_response.json()["code"] == "document_not_found"

