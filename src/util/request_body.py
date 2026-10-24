"""`req.body` / `req.query` / `req.user` equivalents for FastAPI requests."""

from typing import Any

from fastapi import Request

from src.types.auth_types import AuthUserPayload


async def get_body(request: Request) -> dict[str, Any]:
    """Body as parsed by validate_request or file_uploader, else the request.

    Covers what express.json() and express.urlencoded() handled: JSON bodies
    and form-encoded bodies both arrive as a plain dict.
    """
    cached = getattr(request.state, "body", None)
    if cached is not None:
        return cached

    content_type = request.headers.get("content-type", "")
    parsed: Any = {}

    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        parsed = {key: str(value) for key, value in form.multi_items()}
    else:
        body_bytes = await request.body()
        if body_bytes:
            try:
                parsed = await request.json()
            except Exception:
                parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    request.state.body = parsed
    return parsed


def get_query(request: Request) -> dict[str, Any]:
    # "simple" query parsing: last value wins, no nested or bracketed keys
    return dict(request.query_params)


def get_user(request: Request) -> AuthUserPayload | None:
    return getattr(request.state, "user", None)


def get_files(request: Request) -> dict[str, list[dict[str, Any]]]:
    return getattr(request.state, "files", {}) or {}
