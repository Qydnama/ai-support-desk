from fastapi import status


class AppError(Exception):
    status_code: int
    code: str
    message: str

    def __init__(self) -> None:
        super().__init__(self.message)


class UserNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "user_not_found"
    message = "User not found"


class UserEmailAlreadyExistsError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "user_email_already_exists"
    message = "A user with this email already exists"


class OrganizationSlugAlreadyExistsError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "organization_slug_already_exists"
    message = "An organization with this slug already exists"


class OrganizationNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "organization_not_found"
    message = "Organization not found"


class OrganizationMemberAlreadyExistsError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "organization_member_already_exists"
    message = "The user is already a member of this organization"


class OrganizationMemberNotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "organization_member_not_found"
    message = "Organization membership not found"