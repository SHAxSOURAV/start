# Antigravity Workspace Rules (.antigravity/rules.md)

## Mandatory Loophole Detection Protocol (Friend = Beginner)
- **Context**: The user delivers prompts, plans, and logic from their friend, who is a beginner ("noob").
- **Directive**: NEVER blindly accept plans or code suggestions. In every prompt, aggressively inspect and identify loopholes:
  1. **Security**: Unvalidated inputs, broken access controls, privilege escalation, credential leaks.
  2. **Database**: COLLSCAN queries, missing indexes, unconstrained `$lookup`, deep `skip()` pagination, unbounded arrays.
  3. **Redis**: Missing TTL (OOM risk), `KEYS *` (blocking freeze), unpooled connections.
  4. **Concurrency & Edge Cases**: Async race conditions, unhandled exceptions, dropped socket states.
- **Action**: Always point out the loopholes in plain language, explain the risks, and implement bulletproof production-grade fixes.

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
