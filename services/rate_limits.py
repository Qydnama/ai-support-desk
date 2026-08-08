import hashlib
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from core.exceptions import LoginRateLimitExceededError

logger = logging.getLogger(__name__)

LOGIN_RATE_LIMIT_SCRIPT = """
local attempts = redis.call("INCR", KEYS[1])

if attempts == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {attempts, ttl}
"""


def rate_limit_key(
    *,
    scope: str,
    identifier: str,
) -> str:
    identifier_hash = hashlib.sha256(
        identifier.casefold().encode("utf-8"),
    ).hexdigest()

    return f"rate_limit:auth:login:{scope}:v1:{identifier_hash}"


def login_rate_limit_key(email: str) -> str:
    return rate_limit_key(
        scope="email",
        identifier=email,
    )


def login_ip_rate_limit_key(client_ip: str) -> str:
    return rate_limit_key(
        scope="ip",
        identifier=client_ip,
    )


async def enforce_login_rate_limit(
    *,
    redis: Redis,
    email: str,
    max_attempts: int,
    window_seconds: int,
) -> None:
    try:
        attempts, ttl = await redis.eval(
            LOGIN_RATE_LIMIT_SCRIPT,
            1,
            login_rate_limit_key(email),
            window_seconds,
        )
    except RedisError:
        # Fail-open: Redis недоступен, но логин продолжает работать.
        logger.warning(
            "Could not enforce login rate limit",
            exc_info=True,
        )
        return

    if int(attempts) > max_attempts:
        raise LoginRateLimitExceededError(
            retry_after_seconds=max(int(ttl), 1),
        )


async def enforce_login_ip_rate_limit(
    *,
    redis: Redis,
    client_ip: str,
    max_attempts: int,
    window_seconds: int,
) -> None:
    try:
        attempts, ttl = await redis.eval(
            LOGIN_RATE_LIMIT_SCRIPT,
            1,
            login_ip_rate_limit_key(client_ip),
            window_seconds,
        )
    except RedisError:
        logger.warning(
            "Could not enforce login IP rate limit",
            exc_info=True,
        )
        return

    if int(attempts) > max_attempts:
        raise LoginRateLimitExceededError(
            retry_after_seconds=max(int(ttl), 1),
        )


async def clear_login_rate_limit(
    *,
    redis: Redis,
    email: str,
) -> None:
    try:
        await redis.delete(login_rate_limit_key(email))
    except RedisError:
        logger.warning(
            "Could not clear login rate limit",
            exc_info=True,
        )
