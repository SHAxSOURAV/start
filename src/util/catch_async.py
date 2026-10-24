from collections.abc import Awaitable, Callable
from functools import wraps

from fastapi import Request
from fastapi.responses import JSONResponse

from src.util.delete_uploaded_files import delete_uploaded_files

Handler = Callable[[Request], Awaitable[JSONResponse]]


def catch_async(fn: Handler) -> Handler:
    """Deletes files uploaded by a failed request, then re-raises.

    The re-raised error is turned into a response by the global error handler.
    """

    @wraps(fn)
    async def wrapper(request: Request) -> JSONResponse:
        try:
            return await fn(request)
        except Exception:
            delete_uploaded_files(getattr(request.state, "uploaded_files", None))
            request.state.uploaded_files = None
            raise

    return wrapper
