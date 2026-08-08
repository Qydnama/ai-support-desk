# Agent Instructions

## Project invariants

- FastAPI + async SQLAlchemy + PostgreSQL; use the existing `router → service → repository` layering.
- PostgreSQL is the source of truth. Redis is only for cache, rate limits, short-lived coordination, and auxiliary events.
- Preserve authentication, RBAC, tenant isolation, transactions, idempotency, and existing API contracts unless the task explicitly changes one.
- Redis keys must be namespaced, versioned, and tenant-scoped where applicable. Invalidate cache only after a successful PostgreSQL commit.
- Do not replace PostgreSQL constraints, transactions, or the atomic conversation claim with a Redis lock.

## Tool routing

### Graphify

- For codebase or architecture questions, run `graphify query "<question>"` first when `graphify-out/graph.json` exists. Use `graphify path` for relationships and `graphify explain` for one concept.
- Before a verification after the user or agent changed code or tests, run `graphify update .`.
- Dirty `graphify-out/` files are expected. Use the graph; do not treat generated graph changes as a blocker.
- Use `graphify-out/wiki/index.md` for broad navigation when it exists. Read `GRAPH_REPORT.md` only for broad reviews or when the scoped query is insufficient.

### Skills and MCP

- Read a selected skill's `SKILL.md` completely before using it.
- Use `find-skills` only when the user asks to discover or install a capability. Do not install a skill without explicit approval.
- For current library/framework/API documentation, use Context7: resolve the library ID, then query its docs. Do not use it for local business-logic refactors.
- Use available MCP servers only when their capability directly fits the task. Never invent an unavailable server or tool.

## Implementation workflow

- The user writes production code by default. Before proposing a production change: explain the reason, give the exact file and code, then wait for `готово`.
- The assistant may write tests after production code is in place. The assistant may also write production code when the user explicitly asks to do so.
- Keep tests on real PostgreSQL and Redis. Use `REDIS_TEST_URL` (Redis DB 1) for tests; never clear the whole Redis instance.
- Verify with the smallest relevant test first, then run `uv run pytest -q` for regressions. For schema changes run `uv run alembic current` and `uv run alembic check`.

## Repository hygiene

- Preserve unrelated dirty-worktree changes. Never reset, checkout, or delete them.
- Keep `.env` and other secrets out of Git. Commit `.env.example`, `AGENTS.md`, `CLAUDE.md`, `.graphifyignore`, and `skills-lock.json`.
- Keep stable Graphify artifacts (`graph.json`, `GRAPH_REPORT.md`, `manifest.json`) if the team wants a shared map; ignore cache, backups, memory, reflections, and machine-specific hooks.
