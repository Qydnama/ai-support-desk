from collections.abc import Callable
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from core.enums import OrganizationRole

TEST_PASSWORD = "correct-horse-battery-staple"


def authorization_headers(
    client: TestClient,
    email: str,
) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }

def create_user(
    client: TestClient,
    suffix: str,
) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "name": f"User {suffix}",
            "email": f"{suffix}@example.com",
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 201
    return response.json()


def create_organization(
    client: TestClient,
    suffix: str,
) -> dict[str, str]:
    email = f"owner-{suffix}@example.com"
    register_response = client.post(
        "/auth/register",
        json={
            "name": f"Owner {suffix}",
            "email": email,
            "password": TEST_PASSWORD,
        },
    )
    assert register_response.status_code == 201
    response = client.post(
        "/organizations",
        headers=authorization_headers(client, email),
        json={
            "name": f"Organization {suffix}",
            "slug": f"organization-{suffix}",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_contact(
    client: TestClient,
    organization_id: str,
    suffix: str,
    headers: dict[str, str],
) -> dict[str, str]:
    response = client.post(
        f"/organizations/{organization_id}/contacts",
        headers=headers,
        json={
            "name": f"Customer {suffix}",
            "email": f"customer-{suffix}@example.com",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_support_conversation_lifecycle(
    client: TestClient,
    create_stored_membership: Callable[
        [UUID, UUID, OrganizationRole],
        None,
    ],
) -> None:
    agent = create_user(client, "support-agent")
    organization = create_organization(client, "support-lifecycle")
    create_stored_membership(
        UUID(organization["id"]),
        UUID(agent["id"]),
        OrganizationRole.AGENT,
    )
    agent_headers = authorization_headers(
        client,
        agent["email"],
    )
    contact = create_contact(
        client,
        organization["id"],
        "alice",
        agent_headers,
    )

    create_response = client.post(
        "/conversations",
        headers=agent_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Cannot reset password",
        },
    )
    assert create_response.status_code == 201
    conversation = create_response.json()
    conversation_id = conversation["id"]
    assert conversation["status"] == "OPEN"
    assert conversation["contact_id"] == contact["id"]
    assert conversation["assigned_user_id"] is None

    update_response = client.patch(
        f"/conversations/{conversation_id}",
        headers=agent_headers,
        json={
            "status": "PENDING",
            "assigned_user_id": agent["id"],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "PENDING"
    assert update_response.json()["assigned_user_id"] == agent["id"]

    contact_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=agent_headers,
        json={
            "sender_type": "CONTACT",
            "author_contact_id": contact["id"],
            "content": "The reset email never arrives.",
        },
    )
    assert contact_message.status_code == 201

    agent_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=agent_headers,
        json={
            "sender_type": "AGENT",
            "content": "I will check your account.",
        },
    )
    assert agent_message.status_code == 201

    ai_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=agent_headers,
        json={
            "sender_type": "AI",
            "content": "I found an account recovery article.",
        },
    )
    assert ai_message.status_code == 201

    messages_response = client.get(
        f"/conversations/{conversation_id}/messages",
        headers=agent_headers,
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert [message["sender_type"] for message in messages] == [
        "CONTACT",
        "AGENT",
        "AI",
    ]
    assert messages[0]["author_contact_id"] == contact["id"]
    assert messages[1]["author_user_id"] == agent["id"]
    assert messages[2]["author_user_id"] is None
    assert messages[2]["author_contact_id"] is None


def test_conversation_enforces_tenant_and_participants(
    client: TestClient,
) -> None:
    organization = create_organization(client, "tenant-a")
    other_organization = create_organization(client, "tenant-b")
    organization_headers = authorization_headers(
        client,
        "owner-tenant-a@example.com",
    )
    other_organization_headers = authorization_headers(
        client,
        "owner-tenant-b@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "tenant-a",
        organization_headers,
    )
    other_contact = create_contact(
        client,
        other_organization["id"],
        "tenant-b",
        other_organization_headers,
    )
    outsider = create_user(client, "outsider")

    wrong_tenant = client.post(
        "/conversations",
        headers=organization_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": other_contact["id"],
            "subject": "Wrong tenant",
        },
    )
    assert wrong_tenant.status_code == 404
    assert wrong_tenant.json()["code"] == "contact_not_found"

    conversation_response = client.post(
        "/conversations",
        headers=organization_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Correct tenant",
        },
    )
    conversation_id = conversation_response.json()["id"]

    outsider_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=authorization_headers(
            client,
            outsider["email"],
        ),
        json={
            "sender_type": "AGENT",
            "content": "I am not an agent of this organization.",
        },
    )
    assert outsider_message.status_code == 404

    outsider_list = client.get(
        "/conversations",
        headers=authorization_headers(
            client,
            outsider["email"],
        ),
        params={"organization_id": organization["id"]},
    )
    assert outsider_list.status_code == 403
    assert outsider_list.json()["code"] == (
        "organization_member_required"
    )
    assert client.get(
        "/conversations",
        params={"organization_id": organization["id"]},
    ).status_code == 401

    wrong_contact_message = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=organization_headers,
        json={
            "sender_type": "CONTACT",
            "author_contact_id": other_contact["id"],
            "content": "I do not own this conversation.",
        },
    )
    assert wrong_contact_message.status_code == 404

    invalid_author_shape = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=organization_headers,
        json={
            "sender_type": "AI",
            "author_contact_id": contact["id"],
            "content": "AI cannot have a contact author.",
        },
    )
    assert invalid_author_shape.status_code == 422

    forged_agent = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=organization_headers,
        json={
            "sender_type": "AGENT",
            "author_user_id": outsider["id"],
            "content": "Attempt to forge another agent.",
        },
    )
    assert forged_agent.status_code == 422


def test_conversation_validation_not_found_and_cascade(
    client: TestClient,
) -> None:
    organization = create_organization(client, "cascade-conversation")
    owner_headers = authorization_headers(
        client,
        "owner-cascade-conversation@example.com",
    )
    contact = create_contact(
        client,
        organization["id"],
        "cascade",
        owner_headers,
    )

    invalid_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "   ",
        },
    )
    assert invalid_response.status_code == 422

    missing_response = client.get(
        f"/conversations/{uuid4()}",
        headers=owner_headers,
    )
    assert missing_response.status_code == 404

    conversation_response = client.post(
        "/conversations",
        headers=owner_headers,
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Removed with organization",
        },
    )
    conversation_id = conversation_response.json()["id"]

    delete_response = client.delete(
        f"/organizations/{organization['id']}",
        headers=owner_headers,
    )
    assert delete_response.status_code == 204

    removed_response = client.get(
        f"/conversations/{conversation_id}",
        headers=owner_headers,
    )
    assert removed_response.status_code == 404
