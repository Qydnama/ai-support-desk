# AI Support Desk — Project Context

Multi-tenant FastAPI backend for a Zendesk/Intercom-style support desk.

## Architecture

```text
routers → services → repositories → SQLAlchemy models
          ↑
dependencies: auth, DB session, tenant and permission checks
```

- PostgreSQL is the source of truth for users, organizations, conversations, messages, refresh sessions, and idempotency records.
- Redis is an auxiliary system: organization-profile cache, login rate limits, readiness checks, and future short-lived coordination/events.
- All database work is async SQLAlchemy. Repositories do not commit; services own transactions.

## Current Redis implementation

- One `redis.asyncio.Redis` client is created in FastAPI lifespan and closed at shutdown.
- Organization profile uses cache-aside with tenant/permission checks first, 5-minute TTL plus jitter, invalidation after commit, and PostgreSQL fallback.
- Login has atomic Lua rate limits by email and IP; successful login clears only the email failure counter.
- `/health` is liveness; `/ready` checks Redis and PostgreSQL and returns `503` when a dependency is unavailable.
- Tests use `REDIS_TEST_URL` (DB 1); application development uses `REDIS_URL` (DB 0).

## Commands

```powershell
docker compose up -d db redis
uv run fastapi dev main.py
uv run pytest -q
uv run alembic current
uv run alembic check
```

## Agent guidance

`AGENTS.md` is the authoritative executable instruction file for agents. Use Graphify for codebase navigation and Context7 for current external library documentation.

Do not move business data or refresh-session truth to Redis. Do not replace PostgreSQL transactions, idempotency, or atomic conversation claim with Redis locks.
