import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

# Attaches a unique id to every request for log correlation.
# The id is echoed back in the X-Request-Id response header.


async def request_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.id
    return response
