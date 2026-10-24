# server-setup-template (Python)

FastAPI + Beanie + MongoDB backend starter template. A feature-for-feature port
of the Express 5 + TypeScript + Mongoose template: same routes, same
request/response shapes, same status codes, same environment variables, same
socket events.

## Requirements

- Python 3.12+ (or Astral `uv`)
- MongoDB (local, Atlas, or the bundled `docker compose` service)

## Setup

With Astral `uv` (recommended):

```bash
uv sync                       # creates .venv and installs all dependencies + dev tools
cp .env.example .env          # then fill in real values
```

Alternatively, with traditional `venv` & `pip`:

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -e ".[dev]"
cp .env.example .env
```

The schema in [src/config/\_\_init\_\_.py](src/config/__init__.py) validates every
variable at startup; the app prints each problem and exits non-zero on a
mismatch. Keep `.env.example` in sync with it.

## Quick Start

Simply run the startup script in PowerShell:

```powershell
.\start
```

(Or `.\start -Prod` for production mode)

## Commands

Every npm script from the TypeScript template and its Python / uv equivalent:

| npm script | Python (with uv) | Traditional Python |
|---|---|---|
| `npm run dev` (quick) | `.\start` | `uvicorn ...` |
| `npm start` | `uv run python -m src.server` | `python -m src.server` |
| `npm run dev` | `uv run uvicorn src.connection.socket:main_server --reload --host 0.0.0.0 --port 8001` | `uvicorn src.connection.socket:main_server --reload --host 0.0.0.0 --port 8001` |
| `npm run build` / `npm run clean` | not applicable -- Python has no build step | not applicable |
| `npm run typecheck` | `uv run mypy src` | `mypy src` |
| `npm run lint:check` | `uv run ruff check .` | `ruff check .` |
| `npm run lint:fix` | `uv run ruff check --fix .` | `ruff check --fix .` |
| `npm run prettier:check` | `uv run ruff format --check .` | `ruff format --check .` |
| `npm run prettier:fix` | `uv run ruff format .` | `ruff format .` |
| `npm test` | not ported -- see "Not ported" below | not ported |
| `npm run seed:admin` | `uv run python -m src.scripts.seed_super_admin` | `python -m src.scripts.seed_super_admin` |
| `npm run make:file -- <Name>` | `uv run python -m src.util.generate_module <Name>` | `python -m src.util.generate_module <Name>` |

Run every command from the project root: the config loader reads `.env`, and
`docs/openapi.yaml`, `uploads/` and `logs/` are all resolved relative to the
working directory.

## Docker

```bash
docker compose up --build
```

Brings up the API on `:8001` and MongoDB on `:27017`, with named volumes for
`uploads` and `logs`.

## Layout

```
src/
  server.py              entrypoint: connect DB, start jobs, serve, shut down
  application.py         the FastAPI app (routes, middleware, docs, /health)
  config/                env schema + the config object
  connection/            DB connection, Socket.IO server, ASGI composition
  app/
    middleware/          auth, file_uploader, limiter, request_id,
                         validate_request, security_headers, access_log,
                         global_error_handler
    module/<name>/       model, controller, service, routes (+ validation)
    routes/              router mounting for all 8 modules
  builder/               QueryBuilder (search/filter/sort/paginate/fields)
  error/                 ApiError, NotFoundHandler, error translators
  jobs/                  APScheduler cron jobs
  mail/                  HTML email templates
  scripts/               seed_super_admin
  socket/                socket auth, controllers, handlers, emit helpers
  types/                 shared TypedDicts
  util/                  helpers (JWT, logging, responses, validation, ...)
```

Modules mounted at `/api/v1/auth`, `/api/v1/user`, `/api/v1/admin`, `/api/v1/manage`, `/api/v1/notification`,
`/api/v1/feedback`, `/api/v1/review`, `/api/v1/chat`.

## Notes on the port

- **`application.py`, not `app.py`** -- Python cannot have both a `src/app.py`
  module and the `src/app/` package that holds middleware, module and routes.
- **Document fields stay camelCase** (`isActive`, `activationCodeExpire`,
  `profile_image`). They are database and API field names, so renaming them
  would change the contract. Code identifiers are snake_case.
- **Express middleware become FastAPI dependencies.** `auth(...)`,
  `validate_request(...)`, `upload_file()` and the limiters are attached with
  `dependencies=[Depends(...)]` on each route, in the same order as the
  Express chains.
- **`catchAsync` became exception handlers.** Controllers are wrapped with
  `catch_async` for the uploaded-file rollback; the error envelope itself is
  produced by the handlers registered in `global_error_handler.py`.
- **Interactive docs** are served from `docs/openapi.yaml` at `/docs` outside
  production, as before. FastAPI's own generated schema is disabled so the
  checked-in spec stays the single source of truth.

## Not ported

- `tests/` -- the two Vitest suites were intentionally left out of this port.
  `mongodb-memory-server` has no direct Python equivalent; a pytest port would
  need a real MongoDB (via `TEST_MONGO_URL`) or `testcontainers`.
- `docs/*.md` -- the analysis documents from the TypeScript repo.
