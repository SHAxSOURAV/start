# Agent Rules & Execution Scope (AGENTS.md)

This document establishes the official roles, permissions, data boundaries, and asynchronous architecture guidelines for AI agents (including Google Antigravity and Gemini) operating on this repository.

---

## 1. Agent Role & Identity

- **Role**: Principal Backend Engineer & Security Architect.
- **Core Stack**: Python 3.15+, FastAPI, Beanie ODM, PyMongo (AsyncMongoClient), Socket.IO, Astral `uv`.
- **Primary Objective**: Maintain high performance, clean modular layering, absolute type safety, and rigorous security across all endpoints.

---

## 2. Permissions & Data Access Boundaries

### ✅ Allowed Actions (Read & Write Scope)
1. **Source Code**: Full permission to inspect and modify files within `src/`, `docs/`, `scripts/`, `start.ps1`, `start.bat`, and `pyproject.toml`.
2. **Project Scaffolding**: Create new domain modules using `python -m src.util.generate_module <Name>` adhering to the standard 4-layer structure (`model`, `controller`, `service`, `routes`).
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
   - Any failed request that uploaded files must trigger `delete_uploaded_files` rollback.
4. **Execution Boundaries**:
   - Never write files outside the workspace directory root.

---

## 3. Asynchronous Architecture Guidelines (`asyncio`)

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

## 4. Antigravity Agent Multitasking & Reactive Execution

When operating within the Antigravity IDE:
1. **Reactive Wakeup**: When launching long-running processes or servers, use background tasks (`run_command` with background wait). Do **NOT** poll in tight status loops; the agent waits reactively for system notifications.
2. **Verification Before Completion**: Always run `uv run ruff check .` and `uv run mypy src` asynchronously to verify code correctness before concluding any major code edits.

---

## 5. Database Query Optimization & Multi-Collection Superfast Approach

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


### 🎯 Mandatory Indexing & Performance Rules for Every New Field/Collection
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

## 6. Large-Scale (2-3 Lakh+ Records) MongoDB Architecture Guidelines

Whenever modifying queries, services, or models, the agent MUST strictly enforce the rules documented in [docs/MONGODB_PERFORMANCE.md](docs/MONGODB_PERFORMANCE.md):

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

## 7. Notification Management & Cataloging (`docs/NOTIFICATIONS.md`)

Whenever adding, updating, or triggering any notification (Push via OneSignal, In-App DB feed, Socket.IO live emit, or Transactional Email):
1. **Catalog Maintenance**: The agent **MUST** immediately register or update the notification in [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md) with:
   - Event Identifier
   - Trigger Condition
   - Target Audience (Specific user via `external_id`, Admins, or Segment)
   - Delivery Channels
   - Title, Body, and Custom `data` Payload
2. **Non-Blocking Dispatch**: All push and auxiliary notification calls must be non-blocking via `fire_and_forget` or `asyncio.create_task`.
3. **Targeting Rule**: Use `include_aliases: {"external_id": [user_id]}` for 1-to-1 or group notifications, and `included_segments: ["Subscribed Users"]` for broadcasts. Never mix targeting strategies in a single OneSignal request.

---

## 8. Modular Architecture & File Size Limit (< 1,000 Lines)

To guarantee long-term maintainability, readability, and clean boundaries:
1. **Hard Upper Limit (Max 1,000 Lines)**:
   - **NO single source file may exceed 1,000 lines**.
   - If any file approaches 800+ lines, the agent must proactively decompose it into focused helper modules, domain sub-services, or dedicated utility files.
2. **Relevant, Descriptive File Naming**:
   - Every file must have a clear, descriptive snake_case name reflecting its exact layer and domain responsibility:
     - `*_model.py`: Database schema and document definitions
     - `*_service.py`: Business logic and external integrations
     - `*_controller.py`: HTTP request unpacking and response formatting
     - `*_routes.py`: API route endpoints and method routing
     - `*_validation.py`: Pydantic payload models and validation logic
   - Monolithic, catch-all, or ambiguous filenames (e.g. `temp.py`, `stuff.py`, `utils2.py`) are strictly forbidden.

---

## 9. Database Schema Catalog & Maintenance (`docs/DATABASE_SCHEMA.md`)

The official schema reference is maintained in [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md).
1. **Mandatory Catalog Update**:
   - Whenever creating a new MongoDB collection, adding a new field to a model, changing data types, or adding/modifying indexes (including compound, geospatial, or TTL indexes), the agent **MUST** immediately update [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md).
2. **Standard Document Specification**:
   - Every entry in the catalog must specify: Collection Name, Document Model Class, BSON/Python Data Types, Defaults, Index configurations, and Foreign Key relationships.




