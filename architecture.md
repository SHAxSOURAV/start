# System Architectural Blueprint (`architecture.md`)

This document serves as the official, living architectural foundation and single source of truth for this backend workspace. All code contributions, agent tasks, and feature additions must strictly adhere to the patterns and boundaries defined herein.

---

## 1. Project Overview & Core Goals

- **Project Name**: Mount Fuji Backend Server (`server-setup-template`)
- **Primary Goal**: A high-performance, asynchronous, production-ready backend starter template designed to handle high concurrency, real-time communication, and large-scale MongoDB operations (200k–300k+ records).
- **Core Domains Included**:
  - **Authentication & Authorization**: Multi-role JWT auth (User, Driver, Admin, Super Admin), OAuth (Google, Apple), bcrypt password hashing, OTP email verification, password reset flows.
  - **User & Profile Management**: Keyset pagination, profile updates, secure file uploads.
  - **Admin & Platform Management**: System settings, terms & conditions, privacy policy, FAQs, about us, contact us inquiries.
  - **Real-Time Communication**: Bi-directional WebSockets (Socket.IO) for chat rooms, message persistence, online status, and typing indicators.
  - **Notifications**: Multi-channel delivery (OneSignal push, in-app feed, live socket emits, and transactional emails via `aiosmtplib`).
  - **Feedback & Review System**: User rating, feedback categorization, and moderation.
  - **Payments & Subscriptions**: Stripe webhook processing and checkout session management.

---

## 2. Approved Tech Stack & Dependencies

To prevent dependency bloat, version drift, and security vulnerabilities, **only the approved packages listed below are permitted**. No new external dependencies may be added without documenting them in this file and adding them via `uv add`.

| Category | Technology / Library | Version Constraint | Approved Purpose |
|---|---|---|---|
| **Runtime** | Python | `3.15+` (with `3.13` compat) | Core execution engine |
| **Package Manager** | Astral `uv` | Latest | High-speed virtual environments & locking (`uv.lock`) |
| **Web Framework** | FastAPI | `>=0.129.0` | Asynchronous REST routing, OpenAPI generation |
| **ASGI Server** | Uvicorn (standard) | `>=0.54.0` | High-performance ASGI HTTP/WebSocket server |
| **ODM / DB Driver** | Beanie + PyMongo | `beanie>=2.2.0`, `pymongo>=4.19.0` | Async MongoDB ODM (`AsyncMongoClient`) |
| **Data Validation** | Pydantic v2 & Pydantic Settings | `pydantic>=2.14.0`, `pydantic-settings>=2.16.0` | Strict type validation, configuration parsing |
| **Real-Time Engine** | Python-SocketIO & EngineIO | `python-socketio>=5.17.0` | ASGI-mounted WebSocket events & rooms |
| **Task Scheduling** | APScheduler | `apscheduler>=3.11.0` | Async periodic background jobs (`AsyncIOScheduler`) |
| **Email Delivery** | aiosmtplib | `aiosmtplib>=5.1.0` | Non-blocking async SMTP email transmission |
| **Security & Auth** | PyJWT, bcrypt, cryptography | `pyjwt>=2.15.0`, `bcrypt>=5.0.0` | JWT issuance/verification, salt-based hashing |
| **HTTP Client** | HTTPX | `httpx>=0.28.0` | Non-blocking outbound HTTP API requests |
| **Payment Gateway** | Stripe | `stripe>=16.0.0` | Payment intents, billing, and webhooks |
| **Code Quality** | Ruff & Mypy | `ruff>=0.16.0`, `mypy>=2.4.0` | Strict linting, formatting, and static typing |
| **Testing** | pytest, pytest-asyncio, httpx | Standard Dev | Asynchronous unit and integration test suites |

---

## 3. Modular Directory Structure

The project implements a feature-based 4-layer modular architecture under `src/app/module/`, supplemented by shared utilities, connection drivers, and scheduled jobs.

```
start/
├── architecture.md             # This document (System Blueprint)
├── AGENTS.md                   # Always-on Antigravity System Rules
├── pyproject.toml              # Project metadata & dependency declarations
├── uv.lock                     # Deterministic dependency lockfile
├── .python-version             # Python version pin (3.15)
├── .env.example                # Canonical environment variable contract
├── start.ps1 / start.bat       # Cross-platform startup scripts
├── docs/                       # Living architectural catalogs
│   ├── DATABASE_SCHEMA.md      # MongoDB collections & index catalog
│   ├── MONGODB_PERFORMANCE.md  # 2-3 Lakh+ records query guidelines
│   ├── NOTIFICATIONS.md        # Push, socket, and email event catalog
│   └── openapi.yaml            # Single source of truth OpenAPI spec
├── scripts/
│   └── verify_standards.py     # Code style, file size & schema sync validator
└── src/
    ├── server.py               # Application entrypoint & graceful shutdown
    ├── application.py          # FastAPI instance, global middlewares, routing
    ├── config/                 # Pydantic Settings environment configuration
    ├── connection/             # DB & Socket.IO driver initialization
    │   ├── connect_db.py       # Beanie & AsyncMongoClient setup
    │   ├── socket.py           # Combined ASGI App wrapper (FastAPI + Socket.IO)
    │   └── socket_server.py    # Socket.IO AsyncServer singleton
    ├── builder/                # QueryBuilder (filtering, sorting, keyset pagination)
    ├── error/                  # ApiError, global error handlers, custom exceptions
    ├── jobs/                   # Async periodic cron jobs (e.g., OTP cleanup)
    ├── mail/                   # HTML email templates
    ├── socket/                 # Socket event controllers & connection handlers
    ├── types/                  # Cross-cutting TypedDicts and interfaces
    ├── util/                   # Reusable helpers (JWT, logging, responses, fire_and_forget)
    └── app/
        ├── middleware/         # Auth guards, rate limiting, request validation, uploaders
        ├── routes/             # Central route aggregator (`api_v1_router`)
        └── module/             # Self-contained feature modules
            └── <module_name>/
                ├── <name>_model.py       # Database schema & Beanie Document
                ├── <name>_validation.py  # Pydantic request/response payload schemas
                ├── <name>_routes.py      # Route endpoints & middleware attachments
                ├── <name>_controller.py  # Request unpacking & HTTP response formatting
                └── <name>_service.py     # Pure business logic & database queries
```

### Module Scaffolding
New feature modules **must** be created using the official generator:
```powershell
python -m src.util.generate_module <ModuleName>
```
This guarantees that all 5 essential files (`_model.py`, `_validation.py`, `_routes.py`, `_controller.py`, `_service.py`) are scaffolded consistently.

---

## 4. Strict Component Boundaries & Separation of Concerns

Every layer in the system has a singular, non-negotiable responsibility:

```
[ Client Request ]
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. ROUTE LAYER (*_routes.py)                                │
│    - Define HTTP method & URL path                          │
│    - Attach middleware dependencies:                        │
│      Depends(auth(...)), Depends(validate_request(...))     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CONTROLLER LAYER (*_controller.py)                       │
│    - Wrapped with @catch_async for rollback on failure      │
│    - Extract validated inputs from Request / Pydantic models│
│    - Call Service Layer methods                             │
│    - Format response via send_response(...)                 │
│    - ZERO business logic, ZERO direct database queries      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. SERVICE LAYER (*_service.py)                             │
│    - Pure business logic, authorization checks & workflows  │
│    - Fire-and-forget background tasks (emails, notifications│
│    - Query Beanie Documents or native PyMongo collections   │
│    - Raise ApiError for expected client failures            │
│    - ZERO request/response HTTP objects (Request, Response) │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. DATA ACCESS & MODEL LAYER (*_model.py)                   │
│    - Beanie Document class inheriting TimestampedDocument   │
│    - Explicit Settings class defining indexes & collection  │
│    - Enforce projections (e.g. AUTH_PUBLIC_PROJECTION)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow & Standard API Contracts

### 5.1 Success Response Envelope
All successful API endpoints must return a standardized JSON structure via `send_response`:
```json
{
  "statusCode": 200,
  "success": true,
  "message": "Operation completed successfully.",
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 142,
    "totalPage": 8
  }
}
```

### 5.2 Error Response Envelope
Handled centrally by `src/app/middleware/global_error_handler.py`:
```json
{
  "statusCode": 400,
  "success": false,
  "message": "Validation failed.",
  "errorSources": [
    {
      "path": "email",
      "message": "Please provide a valid email address."
    }
  ],
  "stack": "..."
}
```

### 5.3 Error Handling Strategy
- Raise `ApiError(status_code, message)` within service methods for expected business logic violations.
- Unhandled exceptions are automatically captured by `global_error_handler` and converted to a safe `500 Internal Server Error` without leaking sensitive backend details.

---

## 6. Performance & Scalability Rules

1. **Non-Blocking Execution**:
   - Never use blocking synchronous calls (`time.sleep()`, synchronous `requests`, or sync file writes).
   - Auxiliary tasks (emails, notifications, socket broadcasting) must be dispatched using `fire_and_forget`.
2. **Database Querying (Superfast Approach)**:
   - **Embedding**: Embed bounded, tightly coupled items (coordinates, settings).
   - **Links**: Use `Link[Target]` with `fetch_links=True` for single-query entity joins.
   - **Aggregation**: Use native PyMongo pipelines with early `$match` and strict `$project` stages for complex queries.
   - **Indexing**: All queried, sorted, or foreign key fields must have explicit indexes in the model's `Settings.indexes`.
3. **Cursor-Based Pagination**:
   - For collections with 10k+ documents, prefer `_id` or `createdAt` keyset pagination over deep `skip()`.

---

## 7. File Size Hard Limits & Architectural Guardrails

- **Target File Size**: **350–500 lines** per file.
- **Early Refactoring Warning**: If any file reaches **400 lines**, the developer or agent must proactively plan to decompose it into helper sub-modules.
- **Absolute Hard Limit**: **1,000 lines**. No file is permitted to exceed 1,000 lines under any circumstance.
- **Verification Script**: Enforced automatically via `python scripts/verify_standards.py`.
