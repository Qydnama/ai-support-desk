from asyncio import to_thread
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import UserEmailAlreadyExistsError
from core.security import hash_password
from database_errors import is_user_email_unique_violation
from models.users import User
from schemas.auth import RegisterRequest


async def register_user(
    session: AsyncSession,
    data: RegisterRequest,
) -> User:
    password_hash = await to_thread(
        hash_password,
        data.password.get_secret_value(),
    )

    user = User(
        id=uuid4(),
        name=data.name,
        email=str(data.email),
        password_hash=password_hash,
    )

    session.add(user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        if is_user_email_unique_violation(exc):
            raise UserEmailAlreadyExistsError() from exc

        raise
    except Exception:
        await session.rollback()
        raise

    return user