from enum import StrEnum


class ConversationStatus(StrEnum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"


class DocumentStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MessageSenderType(StrEnum):
    CONTACT = "CONTACT"
    AGENT = "AGENT"
    AI = "AI"
    SYSTEM = "SYSTEM"


class OrganizationRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    AGENT = "AGENT"


class OrganizationPermission(StrEnum):
    ORGANIZATION_READ = "organization:read"
    ORGANIZATION_UPDATE = "organization:update"
    ORGANIZATION_DELETE = "organization:delete"

    MEMBER_READ = "member:read"
    MEMBER_CREATE = "member:create"
    MEMBER_DELETE = "member:delete"
    MEMBER_ROLE_UPDATE = "member:role:update"

    CONTACT_READ = "contact:read"
    CONTACT_CREATE = "contact:create"

    DOCUMENT_READ = "document:read"
    DOCUMENT_CREATE = "document:create"

    CONVERSATION_READ = "conversation:read"
    CONVERSATION_CREATE = "conversation:create"
    CONVERSATION_UPDATE = "conversation:update"

    MESSAGE_READ = "message:read"
    MESSAGE_CREATE = "message:create"