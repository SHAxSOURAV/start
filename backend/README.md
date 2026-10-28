# Backend Server (FastAPI + Beanie + MongoDB)

High-performance, asynchronous, production-ready backend starter template built with FastAPI, Beanie ODM, PyMongo, Redis, and Socket.IO.

---

## 1. Requirements & Tech Stack
- **Python**: `>=3.13`
- **Package Manager**: Astral `uv`
- **Framework**: FastAPI `>=0.129.0`
- **ODM / Database**: Beanie `>=2.2.0`, PyMongo `>=4.19.0` (MongoDB 7+)
- **Cache & Revocation**: Redis `>=8.1.0` (asyncio)
- **Real-Time Engine**: Python-SocketIO `>=5.17.0`
- **Cloud Storage**: AWS S3 via `aioboto3`
- **Observability**: Sentry SDK APM tracing & crash reporting

---

## 2. Setup & Environment

Navigate into `backend/`:
```bash
cd backend
uv sync                         # creates .venv and installs all dependencies + dev tools
cp .env.example .env            # fill in local environment variables
```

---

## 3. Quick Start

Run the startup script in PowerShell:
```powershell
cd backend
.\start.ps1
```
Or for production mode:
```powershell
.\start.ps1 -Prod
```

Alternatively, run directly with `uv`:
```bash
uv run uvicorn src.connection.socket:main_server --reload --host 0.0.0.0 --port 8000
```

---

## 4. Development Commands (Run from `backend/`)

| Action | Command |
|---|---|
| **Start Development Server** | `uv run uvicorn src.connection.socket:main_server --reload --host 0.0.0.0 --port 8000` |
| **Start Production Server** | `uv run python -m src.server` |
| **Run Unit & Integration Tests** | `uv run pytest ../tests/backend` |
| **Type Check** | `uv run mypy src` |
| **Lint & Format Check** | `uv run ruff check .` |
| **Auto Fix Lint Issues** | `uv run ruff check --fix .` |
| **Format Code** | `uv run ruff format .` |
| **Seed Super Admin** | `uv run python -m src.scripts.seed_super_admin` |
| **Generate New Module** | `uv run python -m src.util.generate_module <ModuleName>` |

---

## 5. Docker Build

To build and run standalone backend container:
```bash
docker build -t backend-server .
```
Or use the multi-service `docker-compose.yml` located at the root of the monorepo.
