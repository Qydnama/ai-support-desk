from fastapi import APIRouter, Response, status

from dependencies.database import SessionDep
from schemas.auth import RegisterRequest
from schemas.users import UserRead
from services import auth as auth_service

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
async def register_user(
    data: RegisterRequest,
    response: Response,
    session: SessionDep,
) -> UserRead:
    user = await auth_service.register_user(
        session=session,
        data=data,
    )

    response.headers["Location"] = f"/users/{user.id}"

    return UserRead.model_validate(user)