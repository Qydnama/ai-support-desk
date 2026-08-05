class AppError(Exception):
    message: str

    def __init__(self) -> None:
        super().__init__(self.message)


class UserNotFoundError(AppError):
    message = "User not found"


class UserEmailAlreadyExistsError(AppError):
    message = "A user with this email already exists"


class OrganizationSlugAlreadyExistsError(AppError):
    message = "An organization with this slug already exists"


class OrganizationNotFoundError(AppError):
    message = "Organization not found"


class OrganizationMemberAlreadyExistsError(AppError):
    message = "The user is already a member of this organization"


class OrganizationMemberNotFoundError(AppError):
    message = "Organization membership not found"


class ConversationNotFoundError(AppError):
    message = "Conversation not found"


class ConversationMemberRequiredError(AppError):
    message = "The user must be an active organization member"


class ContactNotFoundError(AppError):
    message = "Contact not found"


class ContactEmailAlreadyExistsError(AppError):
    message = "A contact with this email already exists in the organization"


class AuthenticationRequiredError(AppError):
    message = "Authentication credentials are invalid"


class OrganizationMemberRequiredError(AppError):
    message = "The user must be an organization member"


class OrganizationPermissionDeniedError(AppError):
    message = "The user does not have permission for this operation"


class LastOrganizationOwnerError(AppError):
    message = "An organization must have at least one owner"
