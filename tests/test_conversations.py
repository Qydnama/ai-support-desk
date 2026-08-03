from uuid import uuid4

from fastapi.testclient import TestClient


def create_user(
    client: TestClient,
    suffix: str,
) -> dict[str, str]:
    response = client.post(
        "/users",
        json={
            "name": f"User {suffix}",
            "email": f"{suffix}@example.com",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_organization(
    client: TestClient,
    suffix: str,
) -> dict[str, str]:
    response = client.post(
        "/organizations",
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
) -> dict[str, str]:
    response = client.post(
        f"/organizations/{organization_id}/contacts",
        json={
            "name": f"Customer {suffix}",
            "email": f"customer-{suffix}@example.com",
        },
    )
    assert response.status_code == 201
    return response.json()


def add_member(
    client: TestClient,
    organization_id: str,
    user_id: str,
) -> None:
    response = client.post(
        f"/organizations/{organization_id}/members/{user_id}",
    )
    assert response.status_code == 201


def test_support_conversation_lifecycle(
    client: TestClient,
) -> None:
    agent = create_user(client, "support-agent")
    organization = create_organization(client, "support-lifecycle")
    add_member(client, organization["id"], agent["id"])
    contact = create_contact(client, organization["id"], "alice")

    create_response = client.post(
        "/conversations",
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
        json={
            "sender_type": "CONTACT",
            "author_contact_id": contact["id"],
            "content": "The reset email never arrives.",
        },
    )
    assert contact_message.status_code == 201

    agent_message = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "sender_type": "AGENT",
            "author_user_id": agent["id"],
            "content": "I will check your account.",
        },
    )
    assert agent_message.status_code == 201

    ai_message = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "sender_type": "AI",
            "content": "I found an account recovery article.",
        },
    )
    assert ai_message.status_code == 201

    messages_response = client.get(
        f"/conversations/{conversation_id}/messages",
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
    contact = create_contact(client, organization["id"], "tenant-a")
    other_contact = create_contact(
        client,
        other_organization["id"],
        "tenant-b",
    )
    outsider = create_user(client, "outsider")

    wrong_tenant = client.post(
        "/conversations",
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
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Correct tenant",
        },
    )
    conversation_id = conversation_response.json()["id"]

    outsider_message = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "sender_type": "AGENT",
            "author_user_id": outsider["id"],
            "content": "I am not an agent of this organization.",
        },
    )
    assert outsider_message.status_code == 403

    wrong_contact_message = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "sender_type": "CONTACT",
            "author_contact_id": other_contact["id"],
            "content": "I do not own this conversation.",
        },
    )
    assert wrong_contact_message.status_code == 404

    invalid_author_shape = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "sender_type": "AI",
            "author_contact_id": contact["id"],
            "content": "AI cannot have a contact author.",
        },
    )
    assert invalid_author_shape.status_code == 422


def test_conversation_validation_not_found_and_cascade(
    client: TestClient,
) -> None:
    organization = create_organization(client, "cascade-conversation")
    contact = create_contact(client, organization["id"], "cascade")

    invalid_response = client.post(
        "/conversations",
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "   ",
        },
    )
    assert invalid_response.status_code == 422

    missing_response = client.get(f"/conversations/{uuid4()}")
    assert missing_response.status_code == 404

    conversation_response = client.post(
        "/conversations",
        json={
            "organization_id": organization["id"],
            "contact_id": contact["id"],
            "subject": "Removed with organization",
        },
    )
    conversation_id = conversation_response.json()["id"]

    delete_response = client.delete(
        f"/organizations/{organization['id']}",
    )
    assert delete_response.status_code == 204

    removed_response = client.get(f"/conversations/{conversation_id}")
    assert removed_response.status_code == 404
