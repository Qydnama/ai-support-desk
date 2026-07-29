from uuid import UUID

from schemas.users import UserRead

users_by_id: dict[UUID, UserRead] = {}


def is_email_taken(
    email: str,
    *,
    excluding_user_id: UUID | None = None,
) -> bool:
    normalized_email = email.casefold()

    return any(
        existing_user.id != excluding_user_id
        and str(existing_user.email).casefold() == normalized_email
        for existing_user in users_by_id.values()
    )
