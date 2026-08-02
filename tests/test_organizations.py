from collections.abc import Callable
from uuid import UUID

from fastapi.testclient import TestClient

from models.organization_members import OrganizationMember
from models.organizations import Organization
from models.users import User


def create_user(
    client: TestClient,
    *,
    name: str = "Alice",
    email: str = "alice@example.com",
) -> dict[str, str]:
    response = client.post(
        "/users",
        json={
            "name": name,
            "email": email,
        },
    )

    assert response.status_code == 201

    return response.json()


def create_organization(
    client: TestClient,
    *,
    name: str = "Python Developers",
    slug: str = "python-developers",
) -> dict[str, str]:
    response = client.post(
        "/organizations",
        json={
            "name": name,
            "slug": slug,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_create_get_and_list_organization(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/organizations",
        json={
            "name": "Python Developers",
            "slug": "python-developers",
        },
    )

    assert create_response.status_code == 201

    created_organization = create_response.json()
    organization_id = UUID(created_organization["id"])

    assert created_organization == {
        "id": str(organization_id),
        "name": "Python Developers",
        "slug": "python-developers",
    }
    assert create_response.headers["Location"] == (
        f"/organizations/{organization_id}"
    )

    get_response = client.get(
        f"/organizations/{organization_id}",
    )

    assert get_response.status_code == 200
    assert get_response.json() == created_organization

    list_response = client.get("/organizations")

    assert list_response.status_code == 200
    assert list_response.json() == [
        {
            **created_organization,
            "member_count": 0,
        }
    ]


def test_create_organization_with_existing_slug_returns_conflict(
    client: TestClient,
) -> None:
    create_organization(client)

    response = client.post(
        "/organizations",
        json={
            "name": "Another Python Community",
            "slug": "python-developers",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "organization_slug_already_exists",
        "message": "An organization with this slug already exists",
    }


def test_create_organization_rejects_invalid_data(
    client: TestClient,
) -> None:
    response = client.post(
        "/organizations",
        json={
            "name": "   ",
            "slug": "Invalid_Slug",
            "unexpected": True,
        },
    )

    assert response.status_code == 422


def test_get_missing_organization_and_invalid_uuid(
    client: TestClient,
) -> None:
    missing_response = client.get(
        "/organizations/00000000-0000-0000-0000-000000000000",
    )
    invalid_response = client.get(
        "/organizations/not-a-uuid",
    )

    assert missing_response.status_code == 404
    assert missing_response.json() == {
        "code": "organization_not_found",
        "message": "Organization not found",
    }
    assert invalid_response.status_code == 422


def test_update_organization_and_reject_existing_slug(
    client: TestClient,
) -> None:
    first_organization = create_organization(client)
    second_organization = create_organization(
        client,
        name="FastAPI Developers",
        slug="fastapi-developers",
    )

    organization_id = first_organization["id"]

    update_response = client.patch(
        f"/organizations/{organization_id}",
        json={
            "name": "Python Community",
            "slug": "python-community",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json() == {
        "id": organization_id,
        "name": "Python Community",
        "slug": "python-community",
    }

    conflict_response = client.patch(
        f"/organizations/{organization_id}",
        json={
            "slug": second_organization["slug"],
        },
    )

    assert conflict_response.status_code == 409
    assert conflict_response.json() == {
        "code": "organization_slug_already_exists",
        "message": "An organization with this slug already exists",
    }

    stored_response = client.get(
        f"/organizations/{organization_id}",
    )

    assert stored_response.status_code == 200
    assert stored_response.json() == update_response.json()

    null_response = client.patch(
        f"/organizations/{organization_id}",
        json={
            "slug": None,
        },
    )

    assert null_response.status_code == 422


def test_organization_membership_lifecycle(
    client: TestClient,
) -> None:
    organization = create_organization(client)
    user = create_user(client)
    membership_url = (
        f"/organizations/{organization['id']}"
        f"/members/{user['id']}"
    )

    create_response = client.post(membership_url)

    assert create_response.status_code == 201
    assert create_response.json() == {
        "organization_id": organization["id"],
        "user_id": user["id"],
    }
    assert create_response.headers["Location"] == membership_url

    duplicate_response = client.post(membership_url)

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "code": "organization_member_already_exists",
        "message": "The user is already a member of this organization",
    }

    organizations_response = client.get("/organizations")

    assert organizations_response.status_code == 200
    assert organizations_response.json() == [
        {
            **organization,
            "member_count": 1,
        }
    ]

    list_response = client.get(
        f"/organizations/{organization['id']}/members",
    )

    assert list_response.status_code == 200
    assert list_response.json() == [
        {
            "user_id": user["id"],
            "name": "Alice",
            "is_deleted": False,
        }
    ]

    delete_response = client.delete(membership_url)

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    empty_list_response = client.get(
        f"/organizations/{organization['id']}/members",
    )

    assert empty_list_response.status_code == 200
    assert empty_list_response.json() == []

    organizations_response = client.get("/organizations")

    assert organizations_response.status_code == 200
    assert organizations_response.json() == [
        {
            **organization,
            "member_count": 0,
        }
    ]

    missing_response = client.delete(membership_url)

    assert missing_response.status_code == 404
    assert missing_response.json() == {
        "code": "organization_member_not_found",
        "message": "Organization membership not found",
    }


def test_filter_organizations_by_minimum_member_count(
    client: TestClient,
) -> None:
    organization_with_members = create_organization(client)
    empty_organization = create_organization(
        client,
        name="Empty Community",
        slug="empty-community",
    )
    first_user = create_user(client)
    second_user = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )

    for user in (first_user, second_user):
        response = client.post(
            f"/organizations/{organization_with_members['id']}"
            f"/members/{user['id']}",
        )
        assert response.status_code == 201

    zero_response = client.get(
        "/organizations?min_members=0",
    )

    assert zero_response.status_code == 200
    assert {
        organization["id"]: organization["member_count"]
        for organization in zero_response.json()
    } == {
        organization_with_members["id"]: 2,
        empty_organization["id"]: 0,
    }

    one_response = client.get(
        "/organizations?min_members=1",
    )
    two_response = client.get(
        "/organizations?min_members=2",
    )

    for response in (one_response, two_response):
        assert response.status_code == 200
        assert response.json() == [
            {
                **organization_with_members,
                "member_count": 2,
            }
        ]

    three_response = client.get(
        "/organizations?min_members=3",
    )
    invalid_response = client.get(
        "/organizations?min_members=-1",
    )

    assert three_response.status_code == 200
    assert three_response.json() == []
    assert invalid_response.status_code == 422


def test_filter_organizations_by_name_and_slug(
    client: TestClient,
) -> None:
    first_organization = create_organization(client)
    second_organization = create_organization(
        client,
        slug="python-community",
    )
    third_organization = create_organization(
        client,
        name="FastAPI Developers",
        slug="fastapi-developers",
    )

    name_response = client.get(
        "/organizations",
        params={
            "name": "  Python Developers  ",
        },
    )

    assert name_response.status_code == 200
    assert {
        organization["id"]
        for organization in name_response.json()
    } == {
        first_organization["id"],
        second_organization["id"],
    }

    slug_response = client.get(
        "/organizations",
        params={
            "slug": first_organization["slug"],
        },
    )

    assert slug_response.status_code == 200
    assert slug_response.json() == [
        {
            **first_organization,
            "member_count": 0,
        }
    ]

    combined_response = client.get(
        "/organizations",
        params={
            "name": third_organization["name"],
            "slug": first_organization["slug"],
        },
    )

    assert combined_response.status_code == 200
    assert combined_response.json() == []

    invalid_response = client.get(
        "/organizations",
        params={
            "slug": "Invalid_Slug",
        },
    )

    assert invalid_response.status_code == 422


def test_filter_organizations_by_member_user_id(
    client: TestClient,
) -> None:
    first_organization = create_organization(client)
    second_organization = create_organization(
        client,
        name="FastAPI Developers",
        slug="fastapi-developers",
    )
    first_user = create_user(client)
    second_user = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )

    membership_pairs = (
        (first_organization, first_user),
        (first_organization, second_user),
        (second_organization, second_user),
    )

    for organization, user in membership_pairs:
        response = client.post(
            f"/organizations/{organization['id']}"
            f"/members/{user['id']}",
        )
        assert response.status_code == 201

    first_user_response = client.get(
        "/organizations",
        params={
            "member_user_id": first_user["id"],
        },
    )

    assert first_user_response.status_code == 200
    assert first_user_response.json() == [
        {
            **first_organization,
            "member_count": 2,
        }
    ]

    second_user_response = client.get(
        "/organizations",
        params={
            "member_user_id": second_user["id"],
        },
    )

    assert second_user_response.status_code == 200
    assert {
        organization["id"]: organization["member_count"]
        for organization in second_user_response.json()
    } == {
        first_organization["id"]: 2,
        second_organization["id"]: 1,
    }

    missing_response = client.get(
        "/organizations",
        params={
            "member_user_id": (
                "00000000-0000-0000-0000-000000000000"
            ),
        },
    )
    invalid_response = client.get(
        "/organizations",
        params={
            "member_user_id": "not-a-uuid",
        },
    )

    assert missing_response.status_code == 200
    assert missing_response.json() == []
    assert invalid_response.status_code == 422


def test_soft_deleted_user_remains_an_anonymous_member(
    client: TestClient,
) -> None:
    organization = create_organization(client)
    user = create_user(client)
    membership_url = (
        f"/organizations/{organization['id']}"
        f"/members/{user['id']}"
    )

    assert client.post(membership_url).status_code == 201
    assert client.delete(f"/users/{user['id']}").status_code == 204

    response = client.get(
        f"/organizations/{organization['id']}/members",
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "user_id": user["id"],
            "name": "Deleted user",
            "is_deleted": True,
        }
    ]

    remove_response = client.delete(membership_url)

    assert remove_response.status_code == 204


def test_delete_organization_cascades_memberships_only(
    client: TestClient,
    read_stored_user: Callable[[UUID], User | None],
    read_stored_organization: Callable[
        [UUID],
        Organization | None,
    ],
    read_stored_membership: Callable[
        [UUID, UUID],
        OrganizationMember | None,
    ],
) -> None:
    organization = create_organization(client)
    user = create_user(client)
    organization_id = UUID(organization["id"])
    user_id = UUID(user["id"])
    membership_url = (
        f"/organizations/{organization_id}"
        f"/members/{user_id}"
    )

    assert client.post(membership_url).status_code == 201

    delete_response = client.delete(
        f"/organizations/{organization_id}",
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert read_stored_organization(organization_id) is None
    assert read_stored_membership(organization_id, user_id) is None

    stored_user = read_stored_user(user_id)

    assert stored_user is not None
    assert stored_user.deleted_at is None
