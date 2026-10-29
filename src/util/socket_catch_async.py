from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

RED = "\033[31m"
RESET = "\033[0m"

Handler = Callable[..., Awaitable[Any]]


def socket_catch_async(fn: Handler) -> Handler:
    @wraps(fn)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await fn(*args, **kwargs)
        except Exception as error:
            print(f"{RED}\U0001f480 Socket{RESET}", error)
            return None

    return wrapper
