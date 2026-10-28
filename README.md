# Mount Fuji Monorepo

Enterprise-grade, asynchronous monorepo platform encompassing backend API microservices, client application, admin operations dashboard, and public marketing website.

---

## 1. Monorepo Architecture & Directory Layout

```
start/
├── AGENTS.md                   # Always-on Antigravity System Rules & Architectures
├── GEMINI.md                   # Gemini & Agent Guidelines
├── architecture.md             # System Architectural Blueprint
├── CODE_REVIEW.md              # Engineering code review guidelines
├── README.md                   # Monorepo overview and root index
├── docker-compose.yml          # Multi-service orchestrator (Redis, Mongo, Backend, etc.)
├── .gitignore                  # Unified monorepo ignore rules
├── .agents/                    # MCP tools & external agent configuration
│   └── mcp_config.json
├── .antigravity/               # Antigravity agent system configuration
│   └── rules.md
├── docs/                       # Architectural catalogs, schemas, and specifications
│   ├── ASYNC_MONGODB_PRODUCTION_GUIDE.md
│   ├── DATABASE_SCHEMA.md      # MongoDB collections & indexes
│   ├── MEDIA_STORAGE_GUIDELINES.md
│   ├── MONGODB_PERFORMANCE.md  # 200k-300k+ records query guide
│   ├── NOTIFICATIONS.md        # Push, socket & email event catalog
│   ├── openapi.yaml            # Single source of truth OpenAPI spec
│   ├── REDIS_GUIDELINES.md     # Production Redis standards
│   └── SENTRY_MONITORING.md    # Crash reporting & APM tracing
├── scripts/                    # Shared root scripts & quality validators
│   ├── verify_standards.py     # Code standards & file limit validator
│   └── start_redis.ps1
├── tests/                      # Centralized tests organized by service
│   └── backend/                # Backend test suite (pytest)
├── backend/                    # FastAPI + Beanie + MongoDB Asynchronous Backend
│   ├── src/                    # Feature modules & core engine
│   ├── pyproject.toml          # Python package & dependency metadata
│   ├── uv.lock                 # Deterministic dependency lockfile
│   ├── start.ps1               # Backend development launcher
│   └── Dockerfile              # Container image specification
├── frontend/                   # Client-Facing Web Application
│   └── README.md               # Architecture & planned Next.js / React stack
├── dashboard/                  # Admin & Operations Dashboard
│   └── README.md               # Architecture & planned admin portal stack
└── website/                    # Public Marketing Website & Landing Pages
    └── README.md               # Architecture & planned marketing stack
```

---

## 2. Service Overview & Responsibilities

| Service / Directory | Description | Primary Tech Stack |
|---|---|---|
| [backend/](file:///c:/Users/Sourav/Documents/Start/backend) | High-performance async REST & WebSocket API | Python 3.13, FastAPI, Beanie, Redis, Socket.IO |
| [frontend/](file:///c:/Users/Sourav/Documents/Start/frontend) | Client web portal & responsive user interface | Next.js / React, Tailwind CSS, TanStack Query |
| [dashboard/](file:///c:/Users/Sourav/Documents/Start/dashboard) | Admin & Super Admin operations dashboard | Next.js / Vite React, Tailwind CSS, Lucide |
| [website/](file:///c:/Users/Sourav/Documents/Start/website) | Public marketing website & landing pages | Next.js / Astro, Tailwind CSS, SEO JSON-LD |
| [docs/](file:///c:/Users/Sourav/Documents/Start/docs) | Architecture specifications & living API docs | Markdown, OpenAPI YAML |
| [scripts/](file:///c:/Users/Sourav/Documents/Start/scripts) | Root automation & code standard validators | Python, PowerShell |
| [tests/](file:///c:/Users/Sourav/Documents/Start/tests) | End-to-end and integration test suites | Pytest, Playwright |

---

## 3. Git Branching Strategy

This repository adopts a Git-Flow monorepo structure:
- **`develop`**: The primary integration branch containing all service workspaces and root documentation.
- **`backend`**: Dedicated branch for backend core features and API endpoints.
- **`frontend`**: Dedicated branch for the client web application.
- **`dashboard`**: Dedicated branch for the administrative dashboard.
- **`website`**: Dedicated branch for public landing pages and marketing.

---

## 4. Quick Start & Execution

All application services are self-contained. To run the backend:

```powershell
# Navigate to backend
cd backend

# Install dependencies
uv sync

# Launch development server
.\start.ps1
```

To run root standards verification:
```powershell
python scripts/verify_standards.py
```

To run backend tests from root or backend:
```powershell
cd backend
uv run pytest ../tests/backend
```
