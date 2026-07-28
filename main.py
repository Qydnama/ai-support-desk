from typing import Annotated
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, Query, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class UserCreate(UserBase):
    pass


class UserReplace(UserBase):
    pass


class UserUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None

    @field_validator("name", "email")
    @classmethod
    def reject_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Field cannot be null; omit it instead")

        return value


class UserRead(UserBase):
    id: UUID


users_by_id: dict[UUID, UserRead] = {}


def is_email_taken(
    email: str,
    *,
    excluding_user_id: UUID | None = None,
) -> bool:
    normalized_email = str(email).casefold()

    return any(
        existing_user.id != excluding_user_id
        and str(existing_user.email).casefold() == normalized_email
        for existing_user in users_by_id.values()
    )


app = FastAPI(
    title="CRUD API",
    version="0.1.0",
)


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    tags=["health"],
    summary="Check service health",
)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/users",
    status_code=status.HTTP_200_OK,
    tags=["users"],
    summary="List users",
)
async def list_users(
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0),
    ] = 0,
) -> list[UserRead]:
    users = list(users_by_id.values())

    return users[offset : offset + limit]


@app.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    tags=["users"],
    summary="Get a user",
)
async def get_user(user_id: UUID) -> UserRead:
    user = users_by_id.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@app.put(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    tags=["users"],
    summary="Replace a user",
)
async def replace_user(
    user_id: UUID,
    replacement: UserReplace,
) -> UserRead:
    existing_user = users_by_id.get(user_id)

    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if is_email_taken(
        replacement.email,
        excluding_user_id=user_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    replaced_user = UserRead(
        id=user_id,
        **replacement.model_dump(),
    )

    users_by_id[user_id] = replaced_user

    return replaced_user


@app.patch(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    tags=["users"],
    summary="Update a user",
)
async def update_user(
    user_id: UUID,
    update: UserUpdate,
) -> UserRead:
    existing_user = users_by_id.get(user_id)

    if existing_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = update.model_dump(exclude_unset=True)

    if "email" in update_data:
        updated_email = update_data["email"]

        if is_email_taken(
            updated_email,
            excluding_user_id=user_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )

    merged_data = existing_user.model_dump() | update_data
    updated_user = UserRead.model_validate(merged_data)

    users_by_id[user_id] = updated_user

    return updated_user


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
    summary="Delete a user",
)
async def delete_user(user_id: UUID) -> Response:
    if user_id not in users_by_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    del users_by_id[user_id]

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRead,
    tags=["users"],
    summary="Create a user",
)
async def create_user(user: UserCreate) -> UserRead:
    if is_email_taken(user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    created_user = UserRead(
        id=uuid4(),
        **user.model_dump(),
    )

    users_by_id[created_user.id] = created_user

    return created_user
