from uuid import uuid4

from fastapi.testclient import TestClient


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
