from enum import StrEnum


class ConversationStatus(StrEnum):
    OPEN = "OPEN"
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"


class MessageSenderType(StrEnum):
    CONTACT = "CONTACT"
    AGENT = "AGENT"
    AI = "AI"
    SYSTEM = "SYSTEM"
