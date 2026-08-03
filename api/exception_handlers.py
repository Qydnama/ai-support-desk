from dataclasses import dataclass

from fastapi import Request, status
from fastapi.responses import JSONResponse

from core.exceptions import (
    AppError,
    ContactEmailAlreadyExistsError,
    ContactNotFoundError,
    ConversationMemberRequiredError,
    ConversationNotFoundError,
    OrganizationMemberAlreadyExistsError,
    OrganizationMemberNotFoundError,
    OrganizationNotFoundError,
    OrganizationSlugAlreadyExistsError,
    UserEmailAlreadyExistsError,
    UserNotFoundError,
)


@dataclass(frozen=True, slots=True)
class HttpErrorDetails:
    status_code: int
    code: str


HTTP_ERROR_DETAILS: dict[type[AppError], HttpErrorDetails] = {
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
}


async def app_error_handler(
    _request: Request,
    exc: AppError,
) -> JSONResponse:
    details = HTTP_ERROR_DETAILS[type(exc)]

    return JSONResponse(
        status_code=details.status_code,
        content={
            "code": details.code,
            "message": exc.message,
        },
    )
