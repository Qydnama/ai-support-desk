from dataclasses import dataclass

from fastapi import Request, status
from fastapi.responses import JSONResponse

from core.exceptions import (
    AppError,
    AuthenticationRequiredError,
    ContactEmailAlreadyExistsError,
    ContactNotFoundError,
    ConversationAlreadyAssignedError,
    ConversationMemberRequiredError,
    ConversationNotFoundError,
    ConversationVersionConflictError,
    DocumentEncodingInvalidError,
    DocumentFilenameRequiredError,
    DocumentNotFoundError,
    DocumentTooLargeError,
    IdempotencyKeyConflictError,
    LastOrganizationOwnerError,
    LoginRateLimitExceededError,
    OrganizationMemberAlreadyExistsError,
    OrganizationMemberNotFoundError,
    OrganizationMemberRequiredError,
    OrganizationNotFoundError,
    OrganizationPermissionDeniedError,
    OrganizationSlugAlreadyExistsError,
    UnsupportedDocumentContentTypeError,
    UserEmailAlreadyExistsError,
    UserNotFoundError,
)


@dataclass(frozen=True, slots=True)
class HttpErrorDetails:
    status_code: int
    code: str
    headers: dict[str, str] | None = None


HTTP_ERROR_DETAILS: dict[type[AppError], HttpErrorDetails] = {
    AuthenticationRequiredError: HttpErrorDetails(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="authentication_required",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    ),
    ContactNotFoundError: HttpErrorDetails(
        status_code=status.HTTP_404_NOT_FOUND,
        code="contact_not_found",
    ),
    ContactEmailAlreadyExistsError: HttpErrorDetails(
        status_code=status.HTTP_409_CONFLICT,
        code="contact_email_already_exists",
    ),
    ConversationNotFoundError: HttpErrorDetails(
        status_code=status.HTTP_404_NOT_FOUND,
        code="conversation_not_found",
    ),
    ConversationMemberRequiredError: HttpErrorDetails(
        status_code=status.HTTP_403_FORBIDDEN,
        code="conversation_member_required",
    ),
    ConversationAlreadyAssignedError: HttpErrorDetails(
        status_code=status.HTTP_409_CONFLICT,
        code="conversation_already_assigned",
    ),
    ConversationVersionConflictError: HttpErrorDetails(
        status_code=status.HTTP_409_CONFLICT,
        code="conversation_version_conflict",
    ),
    UserNotFoundError: HttpErrorDetails(
        status_code=status.HTTP_404_NOT_FOUND,
        code="user_not_found",
    ),
    UserEmailAlreadyExistsError: HttpErrorDetails(
        status_code=status.HTTP_409_CONFLICT,
        code="user_email_already_exists",
    ),
    OrganizationNotFoundError: HttpErrorDetails(
        status_code=status.HTTP_404_NOT_FOUND,
        code="organization_not_found",
    ),
    OrganizationSlugAlreadyExistsError: HttpErrorDetails(
        status_code=status.HTTP_409_CONFLICT,
        code="organization_slug_already_exists",
    ),
    OrganizationMemberAlreadyExistsError: HttpErrorDetails(
        status_code=status.HTTP_409_CONFLICT,
        code="organization_member_already_exists",
    ),
    OrganizationMemberNotFoundError: HttpErrorDetails(
        status_code=status.HTTP_404_NOT_FOUND,
        code="organization_member_not_found",
    ),
    OrganizationMemberRequiredError: HttpErrorDetails(
        status_code=status.HTTP_403_FORBIDDEN,
        code="organization_member_required",
    ),
    OrganizationPermissionDeniedError: HttpErrorDetails(
        status_code=status.HTTP_403_FORBIDDEN,
        code="organization_permission_denied",
    ),
    LastOrganizationOwnerError: HttpErrorDetails(
        status_code=status.HTTP_409_CONFLICT,
        code="last_organization_owner",
    ),
    IdempotencyKeyConflictError: HttpErrorDetails(
        status_code=status.HTTP_409_CONFLICT,
        code="idempotency_key_conflict",
    ),
    LoginRateLimitExceededError: HttpErrorDetails(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        code="login_rate_limit_exceeded",
    ),
    DocumentNotFoundError: HttpErrorDetails(
        status_code=status.HTTP_404_NOT_FOUND,
        code="document_not_found",
    ),
    DocumentFilenameRequiredError: HttpErrorDetails(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="document_filename_required",
    ),
    UnsupportedDocumentContentTypeError: HttpErrorDetails(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        code="document_content_type_not_supported",
    ),
    DocumentTooLargeError: HttpErrorDetails(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        code="document_too_large",
    ),
    DocumentEncodingInvalidError: HttpErrorDetails(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="document_encoding_invalid",
    ),
}


async def app_error_handler(
    _request: Request,
    exc: AppError,
) -> JSONResponse:
    details = HTTP_ERROR_DETAILS[type(exc)]

    headers = dict(details.headers or {})

    if isinstance(exc, LoginRateLimitExceededError):
        headers["Retry-After"] = str(exc.retry_after_seconds)

    return JSONResponse(
        status_code=details.status_code,
        headers=headers,
        content={
            "code": details.code,
            "message": exc.message,
        },
    )
