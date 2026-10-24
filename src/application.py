"""The FastAPI application (app.ts).

Named application.py because Python cannot have both src/app.py and the
src/app/ package that holds middleware, module and routes.
"""

import time
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
from src.error.not_found_handler import NotFoundHandler
from src.util.cors_options import cors_options

app = FastAPI(
    title="Mount Fuji",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
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


@app.get("/health")
@app.get("/api/v1/health")
async def health() -> JSONResponse:
    db_up = False
    if connect_db.client is not None:
        try:
            await connect_db.client.admin.command("ping")
            db_up = True
        except Exception:
            db_up = False

    return JSONResponse(
        status_code=200 if db_up else 503,
        content={
            "status": "ok" if db_up else "degraded",
            "uptime": time.time() - START_TIME,
            "db": "up" if db_up else "down",
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
