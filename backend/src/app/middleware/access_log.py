"""Morgan equivalent: ":method :url :status :response-time ms - :res[x-request-id]"."""

import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.util.logger import logger


async def access_log(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    started = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - started) * 1000

    url = request.url.path
    if request.url.query:
        url = f"{url}?{request.url.query}"

    request_id = response.headers.get("X-Request-Id") or getattr(
        request.state, "id", ""
    )

    logger.info(
        f"{request.method} {url} {response.status_code} {elapsed:.3f} ms - {request_id}"
    )

    return response
