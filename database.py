from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from settings import settings

engine: AsyncEngine = create_async_engine(
    settings.database_url,
)

session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
)