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