# Antigravity Workspace Rules (.antigravity/rules.md)

## MongoDB & Async Beanie Production Rules
1. **Always Inspect DB First (MCP):** Whenever asked to create, update, or query a Beanie `Document` model or write a FastAPI endpoint involving database operations, ALWAYS use the `mongodb` MCP tools (`collection-schema`, `collection-indexes`, `list-collections`) first to verify the real collection structure and indexes before writing code.
2. **Beanie + Pydantic v2 Syntax:** 
   - Use `Annotated[type, Indexed(...)]` or `IndexModel` inside `class Settings: indexes = [...]`.
   - Always use `.model_dump()` instead of deprecated `.dict()`.
   - Initialize Beanie inside FastAPI's `lifespan` context manager using `AsyncMongoClient` / `AsyncIOMotorClient` with proper connection pooling (`maxPoolSize`, `minPoolSize`).
3. **High-Performance Queries:**
   - Never use `fetch_links=True` in list endpoints.
   - Use `.project(ProjectionModel)` for read-heavy endpoints to avoid loading full documents.
   - Use atomic updates (`await doc.set({...})` or native `update_one`) instead of `.save()` when modifying specific fields.
   - Before writing complex queries or aggregations, check `collection-indexes` via MCP to ensure the query hits an index (no COLLSCAN).

## Redis Production Rules & The 10 Golden Rules
- Strictly follow `docs/REDIS_GUIDELINES.md`. Never use blocking `KEYS *` (always `scan_iter`). Always specify TTL (`ex=`). Always use the centralized connection pool. Wrap all Redis calls in `try/except RedisError` with graceful fallback.
