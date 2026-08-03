from uuid import uuid4

from fastapi.testclient import TestClient


def create_organization(
    client: TestClient,
    suffix: str,
) -> dict[str, str]:
    response = client.post(
        "/organizations",
        json={
            "name": f"Organization {suffix}",
            "slug": f"contacts-{suffix}",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_contact_create_get_and_list(
    client: TestClient,
) -> None:
    organization = create_organization(client, "lifecycle")
    path = f"/organizations/{organization['id']}/contacts"

    create_response = client.post(
        path,
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

    get_response = client.get(f"{path}/{contact['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == contact

    list_response = client.get(path)
    assert list_response.status_code == 200
    assert list_response.json() == [contact]


def test_contact_email_is_unique_inside_organization(
    client: TestClient,
) -> None:
    first_organization = create_organization(client, "unique-a")
    second_organization = create_organization(client, "unique-b")

    for organization, email in (
        (first_organization, "customer@example.com"),
        (second_organization, "CUSTOMER@example.com"),
    ):
        response = client.post(
            f"/organizations/{organization['id']}/contacts",
            json={"name": "Customer", "email": email},
        )
        assert response.status_code == 201

    duplicate = client.post(
        f"/organizations/{first_organization['id']}/contacts",
        json={"name": "Duplicate", "email": "CUSTOMER@example.com"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "contact_email_already_exists"


def test_contact_not_found(
    client: TestClient,
) -> None:
    organization = create_organization(client, "missing")
    response = client.get(
        f"/organizations/{organization['id']}/contacts/{uuid4()}",
    )
    assert response.status_code == 404
    assert response.json()["code"] == "contact_not_found"
