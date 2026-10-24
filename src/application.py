"""The FastAPI application (app.ts).

Named application.py because Python cannot have both src/app.py and the
src/app/ package that holds middleware, module and routes.
"""

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from src.app.middleware.access_log import access_log
from src.app.middleware.global_error_handler import register_error_handlers
from src.app.middleware.request_id import request_id
from src.app.middleware.security_headers import security_headers
from src.app.routes import router as routes
from src.config import config
from src.connection import connect_db
from src.connection.connect_db import disconnect_db
from src.connection.connect_redis import connect_redis, disconnect_redis
from src.error.not_found_handler import NotFoundHandler
from src.jobs import start_jobs, stop_jobs
from src.util.cors_options import cors_options
from src.util.monitoring import init_sentry

# Initialize Sentry APM & Crash Reporting (strictly active only in production/staging)
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    await connect_db.connect_db()
    await connect_redis()
    start_jobs()
    yield
    stop_jobs()
    await disconnect_redis()
    await disconnect_db()


app = FastAPI(
    title="Mount Fuji",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

START_TIME = time.time()


class CachedStaticFiles(StaticFiles):
    """`express.static("uploads", { maxAge: "1d", immutable: true })`"""

    def file_response(self, *args: object, **kwargs: object) -> Response:
        response = super().file_response(*args, **kwargs)  # type: ignore[arg-type]
        response.headers["Cache-Control"] = "public, max-age=86400, immutable"
        return response


# Middleware runs in reverse registration order, so these are added
# bottom-up to match the Express chain: requestId -> helmet -> compression
# -> cors -> morgan
app.add_middleware(BaseHTTPMiddleware, dispatch=access_log)
app.add_middleware(CORSMiddleware, **cors_options)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(BaseHTTPMiddleware, dispatch=security_headers)
app.add_middleware(BaseHTTPMiddleware, dispatch=request_id)

Path("uploads").mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads",
    CachedStaticFiles(directory="uploads", html=False),
    name="uploads",
)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(content="Welcome to Mount Fuji")


@app.get("/health/live")
async def health_live() -> JSONResponse:
    """Liveness probe for Docker, Kubernetes, and container orchestrators.

    Returns 200 OK if the ASGI process is running and event loop is responsive.
    """
    return JSONResponse(
        status_code=200,
        content={"status": "live", "uptime": round(time.time() - START_TIME, 2)},
    )


@app.get("/health")
@app.get("/health/ready")
@app.get("/api/v1/health")
async def health_ready() -> JSONResponse:
    """Readiness probe checking MongoDB and Redis connections with response latency."""
    db_up = False
    db_latency_ms: float | None = None
    if connect_db.client is not None:
        try:
            t0 = time.perf_counter()
            await connect_db.client.admin.command("ping")
            db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            db_up = True
        except Exception:
            db_up = False

    redis_up = False
    redis_latency_ms: float | None = None
    try:
        from src.connection.connect_redis import connect_redis, get_redis_client

        redis_client = get_redis_client()
        if redis_client is None:
            await connect_redis()
            redis_client = get_redis_client()

        if redis_client is not None:
            t0 = time.perf_counter()
            await redis_client.ping()
            redis_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            redis_up = True
    except Exception:
        redis_up = False

    is_healthy = db_up

    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={
            "status": (
                "ok" if (db_up and redis_up) else ("degraded" if db_up else "down")
            ),
            "uptime": round(time.time() - START_TIME, 2),
            "components": {
                "database": {
                    "status": "up" if db_up else "down",
                    "latency_ms": db_latency_ms,
                },
                "redis": {
                    "status": "up" if redis_up else "down",
                    "latency_ms": redis_latency_ms,
                },
            },
        },
    )


# Interactive API docs, outside production only
if config.env != "production":
    openapi_path = Path.cwd() / "docs" / "openapi.yaml"
    if openapi_path.exists():

        @app.get("/docs/openapi.json", include_in_schema=False)
        async def openapi_spec() -> JSONResponse:
            doc = yaml.safe_load(openapi_path.read_text(encoding="utf-8"))
            return JSONResponse(content=doc)

        @app.get("/docs", include_in_schema=False)
        async def swagger_ui() -> Response:
            return get_swagger_ui_html(
                openapi_url="/docs/openapi.json", title="API docs"
            )


app.include_router(routes)

register_error_handlers(app)


@app.exception_handler(StarletteHTTPException)
async def not_found(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code in (404, 405):
        return await NotFoundHandler.handle(request)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )
