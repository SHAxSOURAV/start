# Agent Rules & Execution Scope (AGENTS.md)

@[Architecture](architecture.md)

This document establishes the official roles, permissions, zero-hallucination protocols, file size limits, data boundaries, and asynchronous architecture guidelines for AI agents (including Google Antigravity and Gemini) operating on this repository.

---

## 1. Architectural Reference & Zero-Hallucination Protocol

Every agent turn is governed by the system blueprint in `@[Architecture](architecture.md)`.

### 🛡️ Zero-Hallucination Protocol (Strict Enforcement)
1. **Never Guess or Assume**:
   - **NEVER guess** API signatures, database schemas, collection names, environment variables, or file paths.
   - **NEVER invent** helper functions, third-party libraries, or method names.
2. **Mandatory Inspection Before Action**:
   - Before importing any internal module, check the filesystem (`list_dir`, `view_file`) to verify the file and function exist.
   - Before importing any external package, inspect `pyproject.toml` to verify it is an approved, installed dependency.
   - Before adding any database query or field mutation, cross-reference `docs/DATABASE_SCHEMA.md` and the corresponding `*_model.py`.
   - If an API or requirement is ambiguous, inspect the codebase or use the `ask_question` tool to clarify with the user.
3. **Plan First**:
   - For any multi-file modification or new feature, generate a concise step-by-step plan/artifact outlining affected files and layer boundaries before touching code.
4. **Synchronize Catalogs**:
   - Whenever adding or altering models, collections, or indexes, immediately update `docs/DATABASE_SCHEMA.md`.
   - Whenever adding or changing notifications, immediately update `docs/NOTIFICATIONS.md`.
   - Whenever adding new dependencies or features, immediately update `architecture.md`.

---

## 2. File Size Limits & Modular Boundaries

To guarantee high readability, maintainability, and clean separation of concerns:

1. **Target File Size (350–500 Lines)**:
   - Strive to keep all source files compact and focused, targeting **350–500 lines**.
2. **Proactive Refactoring Trigger (400 Lines)**:
   - If any file exceeds **400 lines** during an edit, the agent must proactively propose a refactoring plan to decompose it into focused helper sub-modules, dedicated sub-services, or validation schemas.
3. **Absolute Hard Limit (1,000 Lines Max)**:
   - **NO single source file may ever exceed 1,000 lines**.
   - Verified automatically before commits via `python scripts/verify_standards.py`.
4. **Single Responsibility & 4-Layer Naming Convention**:
   - Every feature under `src/app/module/<name>/` must maintain strict layer separation:
     - `*_model.py`: Database schema and document definitions
     - `*_service.py`: Business logic and external integrations
     - `*_controller.py`: HTTP request unpacking and response formatting
     - `*_routes.py`: API route endpoints and method routing
     - `*_validation.py`: Pydantic payload models and validation logic
   - Catch-all, monolithic, or ambiguous filenames (e.g. `temp.py`, `stuff.py`, `utils2.py`) are strictly forbidden.

---

## 3. Agent Role & Identity

- **Role**: Principal Backend Engineer & Security Architect.
- **Core Stack**: Python 3.13, FastAPI, Beanie ODM, PyMongo (AsyncMongoClient), Redis (asyncio), Socket.IO, Astral `uv`.
- **Primary Objective**: Maintain high performance, clean modular layering, absolute type safety, and rigorous security across all endpoints.

---

## 4. Permissions & Data Access Boundaries

### ✅ Allowed Actions (Read & Write Scope)
1. **Source Code**: Full permission to inspect and modify files within `src/`, `docs/`, `scripts/`, `start.ps1`, `start.bat`, `pyproject.toml`, `architecture.md`, and `AGENTS.md`.
2. **Project Scaffolding**: Create new domain modules using `python -m src.util.generate_module <Name>` adhering to the standard 4-layer structure (`model`, `controller`, `service`, `routes`, `validation`).
3. **Linting & Type Checking**: Execute `uv run ruff check .` and `uv run mypy src` to ensure clean commits.
4. **Environment Sync**: Execute `uv sync` and `uv add` when dependency changes are requested.

### ⛔ Guarded Boundaries & Restrictions
1. **Credentials & Secrets**:
   - **NEVER** expose, log, or hardcode secrets from `.env` (such as `MONGO_URL`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `SMTP_PASSWORD`).
   - The password field in the `auths` collection must **NEVER** be returned in any API response or log (`AUTH_PUBLIC_PROJECTION = {"password": 0}`).
2. **Database Integrity**:
   - Never execute destructive database drop commands (`drop_database()`, `drop_collection()`) without explicit confirmation.
   - All database queries must run through the configured `DB_NAME` specified in `.env`.
3. **Disk & File Uploads**:
   - File uploads must strictly stay within the `uploads/` directory.
   - Uploaded files must have extensions derived from validated MIME types, never untrusted client filenames.
   - Any failed request that uploaded files must trigger `delete_uploaded_files` rollback via `@catch_async`.
4. **Execution Boundaries**:
   - Never write files outside the workspace directory root.

---

## 5. Asynchronous Architecture Guidelines (`asyncio`)

To prevent event-loop stalls and enable true high-throughput multitasking, the agent must enforce non-blocking asynchronous patterns across the codebase:

### ⚡ Non-Blocking Event Loop Rules
1. **Zero Synchronous I/O**:
   - **FORBIDDEN**: `time.sleep()`, synchronous `requests`, synchronous `pymongo.MongoClient`, or synchronous file I/O in route handlers.
   - **REQUIRED**: `asyncio.sleep()`, `httpx` (async), `pymongo.AsyncMongoClient`, and Beanie async ODM queries (`await Document.find_one(...)`).
2. **Background Multitasking (`fire_and_forget`)**:
   - For auxiliary operations that should not delay HTTP responses (e.g., sending notification emails via `aiosmtplib`, writing audit logs, emitting socket broadcasts), wrap the coroutine with:
     ```python
     from src.util.fire_and_forget import fire_and_forget

     fire_and_forget(post_notification("Title", "Message", user_id))
     ```
   - This dispatches the task immediately via `asyncio.create_task` without blocking client response times.
3. **Scheduled Cron Jobs (`APScheduler`)**:
   - Background periodic tasks (like cleaning expired OTPs) must run via `AsyncIOScheduler` on the running asyncio event loop, never in separate blocking threads or polling loops.
4. **CPU-Intensive Tasks**:
   - Heavy computation (like high-round `bcrypt` hashing) should be mindful of latency or offloaded with `asyncio.to_thread` if blocking thresholds are reached.

---

## 6. Antigravity Agent Multitasking & Reactive Execution

When operating within the Antigravity IDE:
1. **Reactive Wakeup**: When launching long-running processes or servers, use background tasks (`run_command` with background wait). Do **NOT** poll in tight status loops; the agent waits reactively for system notifications.
2. **Verification Before Completion**: Always run `uv run ruff check .` and `uv run mypy src` asynchronously to verify code correctness before concluding any major code edits.

---

## 7. Database Query Optimization & Multi-Collection Superfast Approach

Whenever querying collections, defining relationships, or creating new models/columns in MongoDB, the agent must strictly apply the modern, high-performance two-approach combination:

### 🚀 Approach A: Fast Relations — Embedding vs. Beanie Links (`fetch_links=True`)
1. **Embedding (Zero-Query Join / Denormalization)**:
   - For tightly bound, bounded sub-objects (e.g., coordinates, address, small status history), embed them directly as Pydantic models or lists within the parent document.
   - Zero database joins or lookups needed; resolved in a single document read.
2. **Beanie Link Reference (`Link[TargetDocument]`)**:
   - For distinct entity models (e.g. User -> Posts, Order -> Items):
     ```python
     from beanie import Document, Link


     class Order(Document):
         user: Link[User]
         items: list[Link[Item]] = []
     ```
   - Query using `fetch_links=True` for single-query resolution:
     ```python
     order = await Order.find_one(Order.id == order_id, fetch_links=True)
     ```

### ⚡ Approach B: High-Throughput Aggregations & Joins — Native PyMongo Pipelines
For complex joins, statistics, multi-collection filtering, or reporting, bypass ODM model hydration and execute native async aggregation pipelines on the driver collection:
```python
pipeline = [
    # 1. Join with foreign collection
    {
        "$lookup": {
            "from": "movies",
            "localField": "favorite_movie_ids",
            "foreignField": "_id",
            "as": "movies_details",
        }
    },
    # 2. Strict projection to minimize memory & bandwidth
    {
        "$project": {
            "name": 1,
            "email": 1,
            "movies_details.title": 1,
            "movies_details.genre": 1,
        }
    },
    # 3. Pagination / Limit for high performance
    {"$limit": 50},
]

cursor = User.get_pymongo_collection().aggregate(pipeline)
results = await cursor.to_list(length=50)
```

### 🎯 Mandatory Indexing & Performance Rules
1. **Mandatory Indexing on Foreign Keys**:
   - Every field participating in `$lookup` (`localField` and `foreignField`), search, or sorting MUST be indexed:
     ```python
     from beanie import Indexed

     # Option 1: Inline
     email: Indexed(str, unique=True)


     # Option 2: Settings IndexModel (Hot paths, compound, geospatial)
     class Settings:
         name = "orders"
         indexes = [
             pymongo.IndexModel([("userId", pymongo.ASCENDING)]),
             pymongo.IndexModel([("createdAt", pymongo.DESCENDING)]),
         ]
     ```
2. **Mandatory Projections**:
   - Never retrieve entire unneeded documents across network boundaries. Always use projection dictionaries (`{"password": 0, "__v": 0}`) or `$project` pipeline stages.
3. **Strict Resource Ownership Filtering**:
   - When fetching or mutating any user-owned document by ID, always include the owner in the filter query:
     ```python
     {"_id": ObjectId(resource_id), "user": ObjectId(user_data["userId"])}
     ```

---

## 8. Large-Scale (2-3 Lakh+ Records) MongoDB Architecture Guidelines

Whenever modifying queries, services, or models, the agent MUST strictly enforce the rules documented in `docs/MONGODB_PERFORMANCE.md`:

1. **Strict IXSCAN (Never COLLSCAN)**:
   - Always verify that filtered and sorted fields are indexed so execution uses `IXSCAN`.
   - Use compound indexes for multi-field filtering (e.g. `[("isDeleted", 1), ("deletedAt", 1)]`).
2. **Cursor-Based (Keyset) Pagination**:
   - Avoid massive `skip()`; use `_id` or `createdAt` keyset pagination for O(1) performance.
   - Always project only requested fields.
3. **Denormalization over Repeated Lookups**:
   - Embed small, bounded sub-documents directly instead of multi-collection joins.
4. **Zero N+1 Queries in Async Loops**:
   - FORBIDDEN: `for item in items: await Model.find_one(...)`.
   - REQUIRED: Single query via `{"$in": ids}` or parallel tasks via `asyncio.gather`.
5. **Pipeline Ordering**:
   - Always place `$match` and `$sort` stages BEFORE any `$lookup` or `$group` in aggregation pipelines.
6. **Connection Pooling**:
   - Maintain driver singleton connection pool with pre-configured pool sizes.

---

## 9. Notification Management & Cataloging (`docs/NOTIFICATIONS.md`)

Whenever adding, updating, or triggering any notification (Push via OneSignal, In-App DB feed, Socket.IO live emit, or Transactional Email):
1. **Catalog Maintenance**: The agent **MUST** immediately register or update the notification in `docs/NOTIFICATIONS.md` with:
   - Event Identifier
   - Trigger Condition
   - Target Audience (Specific user via `external_id`, Admins, or Segment)
   - Delivery Channels
   - Title, Body, and Custom `data` Payload
2. **Non-Blocking Dispatch**: All push and auxiliary notification calls must be non-blocking via `fire_and_forget` or `asyncio.create_task`.
3. **Targeting Rule**: Use `include_aliases: {"external_id": [user_id]}` for 1-to-1 or group notifications, and `included_segments: ["Subscribed Users"]` for broadcasts. Never mix targeting strategies in a single OneSignal request.

---

## 10. Database Schema Catalog & Maintenance (`docs/DATABASE_SCHEMA.md`)

The official schema reference is maintained in `docs/DATABASE_SCHEMA.md`.
1. **Mandatory Catalog Update**:
   - Whenever creating a new MongoDB collection, adding a new field to a model, changing data types, or adding/modifying indexes (including compound, geospatial, or TTL indexes), the agent **MUST** immediately update `docs/DATABASE_SCHEMA.md`.
2. **Standard Document Specification**:
   - Every entry in the catalog must specify: Collection Name, Document Model Class, BSON/Python Data Types, Defaults, Index configurations, and Foreign Key relationships.

---

## 11. Latest Industry Standards & Version Enforcement (CRITICAL)

- **Never Use Deprecated Patterns**: Always use the most modern, industry-standard approach for every framework and package.
- **Verify Installed Versions First**: Before writing code for any library, ALWAYS inspect `pyproject.toml`, `requirements.txt`, or `package.json` to check the exact installed version.
- **Live Docs Verification**: If Context7 MCP (`context7`) or Web Search is available, ALWAYS query the latest documentation for the installed version before implementing features or API integrations.
- **Explicit Modern Defaults (Do NOT use legacy alternatives)**:
  - **Python / FastAPI**: Use Pydantic v2 syntax (`model_validate`, `model_dump`, `ConfigDict`), async SQLAlchemy 2.0+ (`select()`, `AsyncSession`), and modern Python 3.10+ type hints (`list[str]`, `str | None`). Never use Pydantic v1 `.dict()` or legacy SQLAlchemy `session.query()`.
  - **MongoDB / Beanie**: Use Python 3.13 async Beanie ODM (`fetch_links=True`, `TimestampedDocument`) or native async PyMongo aggregation pipelines. Never use blocking synchronous pymongo calls.
  - **Next.js / React**: Use App Router, Server Components (RSC), and Server Actions. Never use legacy `pages/` router or `getServerSideProps`.
  - **JavaScript / TypeScript**: Use ES Modules (`import/export`), `async/await`, and strict TypeScript types. Never use `require()` or `any`.
  - **Supabase / Auth**: Use `@supabase/ssr` for authentication and cookie handling. Never use the deprecated `@supabase/auth-helpers`.
- **Package Manager & Terminal Check (Pre-Installation Rule)**:
  - When adding a new dependency, never manually hardcode old versions into `pyproject.toml`, `requirements.txt`, or `package.json`.
  - Always run the CLI command (`uv add <package>` for Python, or `npm install <package>@latest` / `pnpm add <package>@latest` for Node.js) in the terminal so the latest stable version is resolved directly from the registry.
- **Proactive Upgrade Warning**: If asked to use a package or method that is outdated or deprecated in the industry, stop and suggest the modern standard alternative before writing code.

---

## 12. Redis Production Architecture & The 10 Golden Rules Guardrail (`docs/REDIS_GUIDELINES.md`)

All Redis interactions must strictly comply with the **10 Golden Rules for Redis in Production** detailed in [docs/REDIS_GUIDELINES.md](file:///c:/Users/Sourav/Documents/Start/docs/REDIS_GUIDELINES.md).

### 12.1 Mandatory Agent Interception & Warning Protocol
If the user, another agent, or developer requests an unsafe, suboptimal, or dangerous Redis operation:
1. **Immediate Warning**: The agent **MUST IMMEDIATELY WARN** the user before or while implementing, pointing out the production risk (e.g. OOM server crash, full event loop freeze, TCP port exhaustion, or unhandled 500 error cascade).
2. **Best Practice Suggestion**: The agent **MUST PROVIDE THE BEST PRACTICE ALTERNATIVE** immediately and implement the safe version.

### 12.2 Prohibited Patterns & Mandatory Standards
1. **NEVER call `KEYS *` or `.keys()` in production**:
   - *Risk*: Single-threaded Redis freezes, blocking all concurrent API traffic.
   - *Requirement*: Always use cursor-based non-blocking `.scan_iter()` or `RedisService.scan_keys()`.
2. **NEVER set keys without TTL**:
   - *Risk*: RAM fills up over time, resulting in OOM (Out Of Memory) crash.
   - *Requirement*: Always provide explicit TTL (`ex=<seconds>`). If caching DB queries, always add TTL jitter (`add_ttl_jitter`).
3. **NEVER instantiate new Redis connections per request**:
   - *Risk*: Port exhaustion (`Max clients reached` / TCP socket starvation).
   - *Requirement*: Always use the shared singleton connection pool (`get_redis_client()` or `RedisService`). Never call `redis.from_url()` in routes or services.
4. **NEVER delete large collections with synchronous `DEL`**:
   - *Risk*: Blocking Redis thread during memory deallocation.
   - *Requirement*: Use `UNLINK` (`.unlink()`) for asynchronous background thread reclamation.
5. **NEVER use unnamespaced key strings**:
   - *Risk*: Key collisions and inability to audit or flush namespaces.
   - *Requirement*: Keys must follow the colon-separated standard: `<domain>:<entity>:<identifier>` (e.g., `auth:blacklist:jti:<uuid>`, `auth:ban:user:<id>`, `ratelimit:<endpoint>:<ip>`).
6. **Graceful Degradation (Fail-Open / Fallback)**:
   - *Risk*: Temporary Redis restarts crash the entire backend with unhandled `RedisError`.
   - *Requirement*: Wrap operations in `try/except RedisError` with appropriate fallbacks (e.g. `_memory_blacklist` or querying primary database).
7. **Cache Stampede & Avalanche Defense**:
   - *Requirement*: Use distributed locking (`distributed_lock` via `SET NX EX` + Lua unlock) for thundering herd prevention, and 60-second null caching for cache penetration defense.


