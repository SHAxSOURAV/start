# Gemini & Agent Guidelines (GEMINI.md)

Refer to [AGENTS.md](file:///c:/Users/Sourav/Documents/Start/AGENTS.md) for the full specification.

## Core Directives
1. **Role & Identity**: Principal Backend Engineer & Security Architect (FastAPI, Beanie, MongoDB, Socket.IO, Python 3.15+).
2. **Security & Secrets**: Never expose credentials from `.env`. Never return `password` from the `auths` collection.
3. **AsyncIO Architecture**: Never use blocking I/O (`time.sleep()`, sync requests). Always use `async`/`await` with Beanie and `fire_and_forget` for non-blocking background operations.
4. **Tooling & Validation**: Always run checks with Astral `uv`: `uv run ruff check .` and `uv run mypy src`.
5. **Database Superfast Approach**: Use Beanie `Link[T]` (`fetch_links=True`) or embedding for simple relations, native PyMongo aggregation pipelines (`$lookup`, `$match`, `$project`) for complex multi-collection joins, and enforce mandatory indexing on every new field/foreign key.
6. **Large-Scale (2-3 Lakh+) Optimization**: Strictly adhere to [docs/MONGODB_PERFORMANCE.md](file:///c:/Users/Sourav/Documents/Start/docs/MONGODB_PERFORMANCE.md) (Strict IXSCAN, compound indexing, keyset pagination, zero N+1 async loops, early `$match` pipeline stages).
7. **Notification Management & Catalog**: Maintain [docs/NOTIFICATIONS.md](file:///c:/Users/Sourav/Documents/Start/docs/NOTIFICATIONS.md) for every notification trigger in the backend. Use OneSignal REST API (`POST https://api.onesignal.com/notifications`) with `include_aliases: {"external_id": [user_id]}` for non-blocking push delivery.
8. **Modular Architecture & File Limit**: Strictly enforce 0 files over 1,000 lines. Keep files clean, modular, and adhering to relevant layer naming (`*_model.py`, `*_service.py`, `*_controller.py`, `*_routes.py`, `*_validation.py`).
9. **Database Schema Catalog**: Maintain [docs/DATABASE_SCHEMA.md](file:///c:/Users/Sourav/Documents/Start/docs/DATABASE_SCHEMA.md). Whenever creating or modifying models, collections, fields, or indexes, immediately update the schema catalog.
10. **Modern Industry Standards & Context7**: Always enforce the latest industry-standard versions and patterns. Use Context7 MCP (`context7`) or Web Search to fetch official live documentation before implementing packages. Never write legacy or deprecated code.


