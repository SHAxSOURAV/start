# Gemini & Agent Guidelines (GEMINI.md)

Refer to [AGENTS.md](file:///c:/Users/Sourav/Documents/Start/AGENTS.md) for the full specification.

## Core Directives
1. **Role & Identity**: Principal Backend Engineer & Security Architect (FastAPI, Beanie, MongoDB, Socket.IO, Redis, Python 3.13).
2. **Security & Secrets**: Never expose credentials from `.env`. Never return `password` from the `auths` collection.
3. **AsyncIO Architecture**: Never use blocking I/O (`time.sleep()`, sync requests). Always use `async`/`await` with Beanie and `fire_and_forget` for non-blocking background operations.
4. **Tooling & Validation**: Always run checks with Astral `uv`: `uv run ruff check .` and `uv run mypy src`.
5. **Database Superfast Approach**: Use Beanie `Link[T]` (`fetch_links=True`) or embedding for simple relations, native PyMongo aggregation pipelines (`$lookup`, `$match`, `$project`) for complex multi-collection joins, and enforce mandatory indexing on every new field/foreign key.
6. **Large-Scale (2-3 Lakh+) Optimization**: Strictly adhere to [docs/MONGODB_PERFORMANCE.md](file:///c:/Users/Sourav/Documents/Start/docs/MONGODB_PERFORMANCE.md) (Strict IXSCAN, compound indexing, keyset pagination, zero N+1 async loops, early `$match` pipeline stages).
7. **Notification Management & Catalog**: Maintain [docs/NOTIFICATIONS.md](file:///c:/Users/Sourav/Documents/Start/docs/NOTIFICATIONS.md) for every notification trigger in the backend. Use OneSignal REST API (`POST https://api.onesignal.com/notifications`) with `include_aliases: {"external_id": [user_id]}` for non-blocking push delivery.
8. **Modular Architecture & File Limit**: Strictly enforce 0 files over 1,000 lines. Keep files clean, modular, and adhering to relevant layer naming (`*_model.py`, `*_service.py`, `*_controller.py`, `*_routes.py`, `*_validation.py`).
9. **Database Schema Catalog**: Maintain [docs/DATABASE_SCHEMA.md](file:///c:/Users/Sourav/Documents/Start/docs/DATABASE_SCHEMA.md). Whenever creating or modifying models, collections, fields, or indexes, immediately update the schema catalog.
10. **Modern Industry Standards & Context7**: Always enforce the latest industry-standard versions and patterns. Use Context7 MCP (`context7`) or Web Search to fetch official live documentation before implementing packages. Never write legacy or deprecated code.
11. **Production Redis Guardrail & The 10 Golden Rules**: Strictly enforce [docs/REDIS_GUIDELINES.md](file:///c:/Users/Sourav/Documents/Start/docs/REDIS_GUIDELINES.md).
    - **Proactive Warning & Advice**: If the user or any developer asks to perform, or writes, unsafe Redis operations (e.g., `KEYS *` instead of `SCAN`, `.set()` without TTL, creating new connections per request, unnamespaced keys, or unhandled exceptions without fallback), the agent **MUST immediately warn the user**, explain the production hazard (OOM crash, server freeze, socket starvation), and suggest/implement the best practice (e.g. `RedisService`, `cached_get_or_set`, `distributed_lock`, `UNLINK`, `ex=TTL`).
    - **Connection Pooling**: Never call `redis.from_url()` outside `src.connection.connect_redis`; all modules must use the centralized pool.
    - **Fail-Open Graceful Degradation**: Always wrap Redis operations in `try/except RedisError` with fallback handling so Redis downtime never crashes the backend.
12. **MongoDB & Async Beanie Production Rules (Official MongoDB MCP Integration)**:
    - **Always Inspect DB First (MCP)**: Whenever asked to create, update, or query a Beanie `Document` model or write a FastAPI endpoint involving database operations, ALWAYS use the `mongodb` MCP tools (`collection-schema`, `collection-indexes`, `list-collections`) first to verify the real collection structure and indexes before writing code.
    - **Beanie + Pydantic v2 Syntax**: Use `Annotated[type, Indexed(...)]` or `IndexModel` inside `class Settings: indexes = [...]`. Always use `.model_dump()` instead of deprecated `.dict()`. Initialize Beanie inside FastAPI's `lifespan` context manager using `AsyncMongoClient` with proper connection pooling (`maxPoolSize`, `minPoolSize`).
    - **High-Performance Queries**: Never use `fetch_links=True` in list endpoints. Use `.project(ProjectionModel)` for read-heavy endpoints to avoid loading full documents. Use atomic updates (`update_one` / `$set`) instead of full `.save()` when modifying specific fields. Before writing complex queries or aggregations, check `collection-indexes` via MCP to ensure the query hits an index (strict IXSCAN, no COLLSCAN).



