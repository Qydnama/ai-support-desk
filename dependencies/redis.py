from typing import Annotated

import redis.asyncio as redis_asyncio
from fastapi import Depends, Request


def get_redis(request: Request) -> redis_asyncio.Redis:
    return request.app.state.redis

RedisDep = Annotated[redis_asyncio.Redis, Depends(get_redis)]
