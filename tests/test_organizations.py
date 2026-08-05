from collections.abc import Callable
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from core.enums import OrganizationRole
from models.organization_members import OrganizationMember
from models.organizations import Organization
from models.users import User

TEST_PASSWORD = "correct-horse-battery-staple"


def create_user(
    client: TestClient,
    *,
    name: str = "Alice",
    email: str = "alice@example.com",
) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "name": name,
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 201

    return response.json()


def authorization_headers(
    client: TestClient,
    *,
    email: str,
) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    return {
        "Authorization": (
            f"Bearer {response.json()['access_token']}"
        ),
    }


def create_organization(
    client: TestClient,
    *,
    name: str = "Python Developers",
    slug: str = "python-developers",
    owner: dict[str, str] | None = None,
) -> dict[str, str]:
    if owner is None:
        owner_email = "organization-owner@example.com"
        register_response = client.post(
            "/auth/register",
            json={
                "name": "Organization Owner",
                "email": owner_email,
                "password": TEST_PASSWORD,
            },
        )
        assert register_response.status_code in (201, 409)
    else:
        owner_email = owner["email"]
    headers = authorization_headers(client, email=owner_email)
    response = client.post(
        "/organizations",
        headers=headers,
        json={
            "name": name,
            "slug": slug,
        },
    )

    assert response.status_code == 201

    return response.json()


def default_owner_headers(
    client: TestClient,
) -> dict[str, str]:
    return authorization_headers(
        client,
        email="organization-owner@example.com",
    )


def test_create_get_and_list_organization(
    client: TestClient,
    read_stored_membership: Callable[
        [UUID, UUID],
        OrganizationMember | None,
    ],
) -> None:
    owner = create_user(client)
    headers = authorization_headers(
        client,
        email=owner["email"],
    )
    create_response = client.post(
        "/organizations",
        headers=headers,
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
        headers=headers,
    )

    assert get_response.status_code == 200
    assert get_response.json() == created_organization

    list_response = client.get("/organizations", headers=headers)

    assert list_response.status_code == 200
    assert list_response.json() == [
        {
            **created_organization,
            "member_count": 1,
        }
    ]

    owner_membership = read_stored_membership(
        organization_id,
        UUID(owner["id"]),
    )
    assert owner_membership is not None
    assert owner_membership.role is OrganizationRole.OWNER


def test_create_organization_requires_authentication(
    client: TestClient,
) -> None:
    response = client.post(
        "/organizations",
        json={
            "name": "Python Developers",
            "slug": "python-developers",
        },
    )

    assert response.status_code == 401


def test_organization_reads_are_tenant_scoped(
    client: TestClient,
) -> None:
    alice = create_user(client)
    bob = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    alice_organization = create_organization(
        client,
        owner=alice,
    )
    bob_organization = create_organization(
        client,
        name="Bob Organization",
        slug="bob-organization",
        owner=bob,
    )
    alice_headers = authorization_headers(
        client,
        email=alice["email"],
    )

    list_response = client.get(
        "/organizations",
        headers=alice_headers,
    )
    foreign_response = client.get(
        f"/organizations/{bob_organization['id']}",
        headers=alice_headers,
    )

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [
        alice_organization["id"],
    ]
    assert foreign_response.status_code == 403
    assert client.get("/organizations").status_code == 401


def test_create_organization_with_existing_slug_returns_conflict(
    client: TestClient,
) -> None:
    create_organization(client)
    owner = create_user(
        client,
        email="second-owner@example.com",
    )

    response = client.post(
        "/organizations",
        headers=authorization_headers(
            client,
            email=owner["email"],
        ),
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
    owner = create_user(client)
    response = client.post(
        "/organizations",
        headers=authorization_headers(
            client,
            email=owner["email"],
        ),
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
    user = create_user(client)
    headers = authorization_headers(client, email=user["email"])
    missing_response = client.get(
        "/organizations/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    invalid_response = client.get(
        "/organizations/not-a-uuid",
        headers=headers,
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
    owner = create_user(client)
    auth_headers = authorization_headers(
        client,
        email=owner["email"],
    )
    first_organization = create_organization(
        client,
        owner=owner,
    )
    second_organization = create_organization(
        client,
        name="FastAPI Developers",
        slug="fastapi-developers",
    )

    organization_id = first_organization["id"]

    update_response = client.patch(
        f"/organizations/{organization_id}",
        headers=auth_headers,
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
        headers=auth_headers,
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
        headers=auth_headers,
    )

    assert stored_response.status_code == 200
    assert stored_response.json() == update_response.json()

    null_response = client.patch(
        f"/organizations/{organization_id}",
        headers=auth_headers,
        json={
            "slug": None,
        },
    )

    assert null_response.status_code == 422


def test_organization_update_and_delete_permissions(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    owner = create_user(client)
    organization = create_organization(
        client,
        owner=owner,
    )
    organization_id = UUID(organization["id"])
    admin = create_user(
        client,
        name="Admin",
        email="admin@example.com",
    )
    agent = create_user(
        client,
        name="Agent",
        email="agent@example.com",
    )
    create_stored_membership(
        organization_id,
        UUID(admin["id"]),
        OrganizationRole.ADMIN,
    )
    create_stored_membership(
        organization_id,
        UUID(agent["id"]),
        OrganizationRole.AGENT,
    )
    path = f"/organizations/{organization_id}"

    unauthenticated_update = client.patch(
        path,
        json={"name": "Forbidden update"},
    )
    agent_update = client.patch(
        path,
        headers=authorization_headers(
            client,
            email=agent["email"],
        ),
        json={"name": "Forbidden update"},
    )
    admin_update = client.patch(
        path,
        headers=authorization_headers(
            client,
            email=admin["email"],
        ),
        json={"name": "Updated by admin"},
    )
    admin_delete = client.delete(
        path,
        headers=authorization_headers(
            client,
            email=admin["email"],
        ),
    )

    assert unauthenticated_update.status_code == 401
    assert agent_update.status_code == 403
    assert agent_update.json()["code"] == (
        "organization_permission_denied"
    )
    assert admin_update.status_code == 200
    assert admin_update.json()["name"] == "Updated by admin"
    assert admin_delete.status_code == 403
    assert admin_delete.json()["code"] == (
        "organization_permission_denied"
    )


def test_organization_membership_lifecycle(
    client: TestClient,
    read_stored_membership: Callable[
        [UUID, UUID],
        OrganizationMember | None,
    ],
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    organization = create_organization(client)
    admin = create_user(client)
    user = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    organization_id = UUID(organization["id"])
    create_stored_membership(
        organization_id,
        UUID(admin["id"]),
        OrganizationRole.ADMIN,
    )
    auth_headers = authorization_headers(
        client,
        email=admin["email"],
    )
    membership_url = (
        f"/organizations/{organization['id']}"
        f"/members/{user['id']}"
    )

    create_response = client.post(
        membership_url,
        headers=auth_headers,
    )

    assert create_response.status_code == 201
    assert create_response.json() == {
        "organization_id": organization["id"],
        "user_id": user["id"],
        "role": "AGENT",
    }
    assert create_response.headers["Location"] == membership_url

    stored_membership = read_stored_membership(
        organization_id,
        UUID(user["id"]),
    )

    assert stored_membership is not None
    assert stored_membership.role is OrganizationRole.AGENT

    duplicate_response = client.post(
        membership_url,
        headers=auth_headers,
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "code": "organization_member_already_exists",
        "message": "The user is already a member of this organization",
    }

    organizations_response = client.get(
        "/organizations",
        headers=auth_headers,
    )

    assert organizations_response.status_code == 200
    assert organizations_response.json() == [
        {
            **organization,
            "member_count": 3,
        }
    ]

    list_response = client.get(
        f"/organizations/{organization['id']}/members",
        headers=auth_headers,
    )

    assert list_response.status_code == 200
    members_by_id = {
        member["user_id"]: member
        for member in list_response.json()
    }
    assert members_by_id[user["id"]] == {
        "user_id": user["id"],
        "name": "Bob",
        "role": "AGENT",
        "is_deleted": False,
    }

    delete_response = client.delete(
        membership_url,
        headers=auth_headers,
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    empty_list_response = client.get(
        f"/organizations/{organization['id']}/members",
        headers=auth_headers,
    )

    assert empty_list_response.status_code == 200
    remaining_member_ids = [
        member["user_id"]
        for member in empty_list_response.json()
    ]
    assert admin["id"] in remaining_member_ids
    assert len(remaining_member_ids) == 2

    organizations_response = client.get(
        "/organizations",
        headers=auth_headers,
    )

    assert organizations_response.status_code == 200
    assert organizations_response.json() == [
        {
            **organization,
            "member_count": 2,
        }
    ]

    missing_response = client.delete(
        membership_url,
        headers=auth_headers,
    )

    assert missing_response.status_code == 404
    assert missing_response.json() == {
        "code": "organization_member_not_found",
        "message": "Organization membership not found",
    }


def test_filter_organizations_by_minimum_member_count(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
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
        create_stored_membership(
            UUID(organization_with_members["id"]),
            UUID(user["id"]),
            OrganizationRole.AGENT,
        )

    zero_response = client.get(
        "/organizations?min_members=0",
        headers=default_owner_headers(client),
    )

    assert zero_response.status_code == 200
    assert {
        organization["id"]: organization["member_count"]
        for organization in zero_response.json()
    } == {
        organization_with_members["id"]: 3,
        empty_organization["id"]: 1,
    }

    one_response = client.get(
        "/organizations?min_members=1",
        headers=default_owner_headers(client),
    )
    two_response = client.get(
        "/organizations?min_members=2",
        headers=default_owner_headers(client),
    )

    assert one_response.status_code == 200
    assert {
        organization["id"]
        for organization in one_response.json()
    } == {
        organization_with_members["id"],
        empty_organization["id"],
    }
    assert two_response.status_code == 200
    assert two_response.json() == [
        {
            **organization_with_members,
            "member_count": 3,
        }
    ]

    three_response = client.get(
        "/organizations?min_members=3",
        headers=default_owner_headers(client),
    )
    invalid_response = client.get(
        "/organizations?min_members=-1",
        headers=default_owner_headers(client),
    )

    assert three_response.status_code == 200
    assert three_response.json() == [
        {
            **organization_with_members,
            "member_count": 3,
        }
    ]
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
        headers=default_owner_headers(client),
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
        headers=default_owner_headers(client),
        params={
            "slug": first_organization["slug"],
        },
    )

    assert slug_response.status_code == 200
    assert slug_response.json() == [
        {
            **first_organization,
            "member_count": 1,
        }
    ]

    combined_response = client.get(
        "/organizations",
        headers=default_owner_headers(client),
        params={
            "name": third_organization["name"],
            "slug": first_organization["slug"],
        },
    )

    assert combined_response.status_code == 200
    assert combined_response.json() == []

    invalid_response = client.get(
        "/organizations",
        headers=default_owner_headers(client),
        params={
            "slug": "Invalid_Slug",
        },
    )

    assert invalid_response.status_code == 422


def test_filter_organizations_by_member_user_id(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
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
        create_stored_membership(
            UUID(organization["id"]),
            UUID(user["id"]),
            OrganizationRole.AGENT,
        )

    first_user_response = client.get(
        "/organizations",
        headers=default_owner_headers(client),
        params={
            "member_user_id": first_user["id"],
        },
    )

    assert first_user_response.status_code == 200
    assert first_user_response.json() == [
        {
            **first_organization,
            "member_count": 3,
        }
    ]

    second_user_response = client.get(
        "/organizations",
        headers=default_owner_headers(client),
        params={
            "member_user_id": second_user["id"],
        },
    )

    assert second_user_response.status_code == 200
    assert {
        organization["id"]: organization["member_count"]
        for organization in second_user_response.json()
    } == {
        first_organization["id"]: 3,
        second_organization["id"]: 2,
    }

    missing_response = client.get(
        "/organizations",
        headers=default_owner_headers(client),
        params={
            "member_user_id": (
                "00000000-0000-0000-0000-000000000000"
            ),
        },
    )
    invalid_response = client.get(
        "/organizations",
        headers=default_owner_headers(client),
        params={
            "member_user_id": "not-a-uuid",
        },
    )

    assert missing_response.status_code == 200
    assert missing_response.json() == []
    assert invalid_response.status_code == 422


def test_soft_deleted_user_remains_an_anonymous_member(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    organization = create_organization(client)
    user = create_user(client)
    viewer = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    membership_url = (
        f"/organizations/{organization['id']}"
        f"/members/{user['id']}"
    )
    viewer_membership_url = (
        f"/organizations/{organization['id']}"
        f"/members/{viewer['id']}"
    )

    create_stored_membership(
        UUID(organization["id"]),
        UUID(user["id"]),
        OrganizationRole.AGENT,
    )
    create_stored_membership(
        UUID(organization["id"]),
        UUID(viewer["id"]),
        OrganizationRole.ADMIN,
    )
    auth_headers = authorization_headers(
        client,
        email=viewer["email"],
    )
    assert client.delete(
        f"/users/{user['id']}",
        headers=authorization_headers(
            client,
            email=user["email"],
        ),
    ).status_code == 204

    response = client.get(
        f"/organizations/{organization['id']}/members",
        headers=auth_headers,
    )

    assert response.status_code == 200
    members_by_id = {
        member["user_id"]: member
        for member in response.json()
    }
    assert members_by_id[user["id"]] == {
        "user_id": user["id"],
        "name": "Deleted user",
        "role": "AGENT",
        "is_deleted": True,
    }

    remove_response = client.delete(
        membership_url,
        headers=auth_headers,
    )

    assert remove_response.status_code == 204


def test_member_cannot_list_another_organizations_members(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    user = create_user(client)
    first_organization = create_organization(client)
    second_organization = create_organization(
        client,
        name="Other Organization",
        slug="other-organization",
    )
    membership_url = (
        f"/organizations/{first_organization['id']}"
        f"/members/{user['id']}"
    )

    create_stored_membership(
        UUID(first_organization["id"]),
        UUID(user["id"]),
        OrganizationRole.AGENT,
    )

    auth_headers = authorization_headers(
        client,
        email=user["email"],
    )
    response = client.get(
        f"/organizations/{second_organization['id']}/members",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "organization_member_required",
        "message": "The user must be an organization member",
    }


def test_agent_cannot_add_organization_member(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    organization = create_organization(client)
    agent = create_user(client)
    target = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    create_stored_membership(
        UUID(organization["id"]),
        UUID(agent["id"]),
        OrganizationRole.AGENT,
    )
    auth_headers = authorization_headers(
        client,
        email=agent["email"],
    )

    response = client.post(
        f"/organizations/{organization['id']}"
        f"/members/{target['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 403
    assert response.json() == {
        "code": "organization_permission_denied",
        "message": (
            "The user does not have permission for this operation"
        ),
    }


def test_owner_can_add_organization_member(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    organization = create_organization(client)
    owner = create_user(client)
    target = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    create_stored_membership(
        UUID(organization["id"]),
        UUID(owner["id"]),
        OrganizationRole.OWNER,
    )
    auth_headers = authorization_headers(
        client,
        email=owner["email"],
    )

    response = client.post(
        f"/organizations/{organization['id']}"
        f"/members/{target['id']}",
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert response.json()["role"] == "AGENT"


def test_adding_member_requires_authentication(
    client: TestClient,
) -> None:
    organization = create_organization(client)
    target = create_user(client)

    response = client.post(
        f"/organizations/{organization['id']}"
        f"/members/{target['id']}",
    )

    assert response.status_code == 401


def test_owner_can_update_member_role_and_permissions_apply_immediately(
    client: TestClient,
    read_stored_membership: Callable[
        [UUID, UUID],
        OrganizationMember | None,
    ],
) -> None:
    owner = create_user(client)
    organization = create_organization(client, owner=owner)
    member = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    new_member = create_user(
        client,
        name="Charlie",
        email="charlie@example.com",
    )
    owner_headers = authorization_headers(
        client,
        email=owner["email"],
    )
    membership_url = (
        f"/organizations/{organization['id']}"
        f"/members/{member['id']}"
    )
    assert client.post(
        membership_url,
        headers=owner_headers,
    ).status_code == 201

    role_response = client.patch(
        membership_url,
        headers=owner_headers,
        json={"role": "ADMIN"},
    )

    assert role_response.status_code == 200
    assert role_response.json()["role"] == "ADMIN"
    stored_membership = read_stored_membership(
        UUID(organization["id"]),
        UUID(member["id"]),
    )
    assert stored_membership is not None
    assert stored_membership.role is OrganizationRole.ADMIN

    admin_headers = authorization_headers(
        client,
        email=member["email"],
    )
    assert client.post(
        f"/organizations/{organization['id']}"
        f"/members/{new_member['id']}",
        headers=admin_headers,
    ).status_code == 201
    assert client.patch(
        membership_url,
        headers=admin_headers,
        json={"role": "OWNER"},
    ).status_code == 403

    demote_response = client.patch(
        membership_url,
        headers=owner_headers,
        json={"role": "AGENT"},
    )
    assert demote_response.status_code == 200
    assert demote_response.json()["role"] == "AGENT"

    another_member = create_user(
        client,
        name="Dana",
        email="dana@example.com",
    )
    denied_after_demotion = client.post(
        f"/organizations/{organization['id']}"
        f"/members/{another_member['id']}",
        headers=admin_headers,
    )
    assert denied_after_demotion.status_code == 403


def test_last_owner_cannot_be_demoted_or_removed(
    client: TestClient,
) -> None:
    owner = create_user(client)
    organization = create_organization(client, owner=owner)
    headers = authorization_headers(client, email=owner["email"])
    membership_url = (
        f"/organizations/{organization['id']}"
        f"/members/{owner['id']}"
    )

    demote_response = client.patch(
        membership_url,
        headers=headers,
        json={"role": "ADMIN"},
    )
    remove_response = client.delete(
        membership_url,
        headers=headers,
    )

    for response in (demote_response, remove_response):
        assert response.status_code == 409
        assert response.json() == {
            "code": "last_organization_owner",
            "message": "An organization must have at least one owner",
        }


def test_admin_cannot_remove_owner(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    owner = create_user(client)
    organization = create_organization(client, owner=owner)
    admin = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    create_stored_membership(
        UUID(organization["id"]),
        UUID(admin["id"]),
        OrganizationRole.ADMIN,
    )

    response = client.delete(
        f"/organizations/{organization['id']}"
        f"/members/{owner['id']}",
        headers=authorization_headers(
            client,
            email=admin["email"],
        ),
    )

    assert response.status_code == 403
    assert response.json()["code"] == (
        "organization_permission_denied"
    )


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
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    owner = create_user(client)
    organization = create_organization(
        client,
        owner=owner,
    )
    user = create_user(
        client,
        name="Bob",
        email="bob@example.com",
    )
    organization_id = UUID(organization["id"])
    user_id = UUID(user["id"])
    membership_url = (
        f"/organizations/{organization_id}"
        f"/members/{user_id}"
    )

    create_stored_membership(
        organization_id,
        user_id,
        OrganizationRole.AGENT,
    )

    delete_response = client.delete(
        f"/organizations/{organization_id}",
        headers=authorization_headers(
            client,
            email=owner["email"],
        ),
    )

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert read_stored_organization(organization_id) is None
    assert read_stored_membership(organization_id, user_id) is None

    stored_user = read_stored_user(user_id)

    assert stored_user is not None
    assert stored_user.deleted_at is None
