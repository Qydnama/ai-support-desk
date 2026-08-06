from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.exc import IntegrityError

USER_EMAIL_UNIQUE_INDEX = "uq_users_email_ci"
ORGANIZATION_SLUG_UNIQUE_CONSTRAINT = "uq_organizations_slug"
ORGANIZATION_MEMBER_PRIMARY_KEY = "organization_members_pkey"
CONTACT_EMAIL_UNIQUE_INDEX = "uq_contacts_organization_email_ci"
IDEMPOTENCY_RECORD_ORGANIZATION_KEY_UNIQUE_CONSTRAINT = (
    "uq_idempotency_records_organization_key"
)


def is_user_email_unique_violation(
    exc: IntegrityError,
) -> bool:
    postgres_error = exc.orig.__cause__

    return (
        isinstance(postgres_error, UniqueViolationError)
        and postgres_error.constraint_name == USER_EMAIL_UNIQUE_INDEX
    )


def is_organization_slug_unique_violation(
    exc: IntegrityError,
) -> bool:
    postgres_error = exc.orig.__cause__

    return (
        isinstance(postgres_error, UniqueViolationError)
        and postgres_error.constraint_name
        == ORGANIZATION_SLUG_UNIQUE_CONSTRAINT
    )


def is_organization_member_primary_key_violation(
    exc: IntegrityError,
) -> bool:
    postgres_error = exc.orig.__cause__

    return (
        isinstance(postgres_error, UniqueViolationError)
        and postgres_error.constraint_name
        == ORGANIZATION_MEMBER_PRIMARY_KEY
    )


def is_contact_email_unique_violation(
    exc: IntegrityError,
) -> bool:
    postgres_error = exc.orig.__cause__

    return (
        isinstance(postgres_error, UniqueViolationError)
        and postgres_error.constraint_name
        == CONTACT_EMAIL_UNIQUE_INDEX
    )


def is_idempotency_record_organization_key_unique_violation(
    exc: IntegrityError,
) -> bool:
    postgres_error = exc.orig.__cause__

    return (
        isinstance(postgres_error, UniqueViolationError)
        and postgres_error.constraint_name
        == IDEMPOTENCY_RECORD_ORGANIZATION_KEY_UNIQUE_CONSTRAINT
    )