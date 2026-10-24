import inspect
import time
from collections.abc import Awaitable, Callable

from fastapi import Request

from src.error.api_error import ApiError
from src.util.http_status import status
from src.util.request_body import get_body

# Fixed-window counters, in process memory -- the same storage model
# express-rate-limit uses by default.
_windows: dict[tuple[int, str], tuple[float, int]] = {}


class RateLimitError(ApiError):
    def __init__(
        self,
        reset_seconds: int,
        limit: int,
        window_ms: int,
        message: str | None = None,
    ) -> None:
        super().__init__(
            status.TOO_MANY_REQUESTS,
            message or "Too many requests please try again later",
        )
        self.reset_seconds = reset_seconds
        self.limit = limit
        self.window_ms = window_ms


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def create_limiter(
    window_ms: int = 60 * 60 * 1000,
    limit: int = 10,
    key_func: Callable[[Request], Awaitable[str | None] | str | None] | None = None,
    message: str | None = None,
) -> Callable[[Request], Awaitable[None]]:
    limiter_id = id(object())

    async def dependency(request: Request) -> None:
        key_identifier: str | None = None
        if key_func is not None:
            res = key_func(request)
            if inspect.isawaitable(res):
                key_identifier = await res
            else:
                key_identifier = res  # type: ignore[assignment]

        if not key_identifier:
            key_identifier = _get_client_ip(request)

        key = (limiter_id, key_identifier)
        now = time.time()
        window_seconds = window_ms / 1000

        started_at, count = _windows.get(key, (now, 0))
        if now - started_at >= window_seconds:
            started_at, count = now, 0

        count += 1
        _windows[key] = (started_at, count)

        if count > limit:
            reset = int(started_at + window_seconds - now)
            raise RateLimitError(max(reset, 0), limit, window_ms, message=message)

    return dependency


async def _extract_email_key(request: Request) -> str | None:
    try:
        body = await get_body(request)
        email = body.get("email")
        if email and isinstance(email, str):
            return f"email:{email.strip().lower()}"
    except Exception:
        pass
    return None


def create_email_cooldown_limiter(
    cooldown_seconds: float = 5.0,
    message: str | None = None,
) -> Callable[[Request], Awaitable[None]]:
    """Enforces a strict minimum cooldown between requests for the same email address."""
    sec = int(cooldown_seconds)
    msg = (
        message
        or f"Too many attempts for this email. Please wait {sec} seconds before trying again."
    )
    return create_limiter(
        window_ms=int(cooldown_seconds * 1000),
        limit=1,
        key_func=_extract_email_key,
        message=msg,
    )


# --- Pre-configured guards for Auth endpoints ---
limiter = create_limiter()
login_limiter = create_limiter(
    window_ms=15 * 60 * 1000,
    limit=10,
    message="Too many sign-in attempts from this IP address. Please try again after 15 minutes.",
)
login_email_cooldown_limiter = create_email_cooldown_limiter(
    cooldown_seconds=3.0,
    message="Too many rapid attempts for this account. Please wait 3 seconds before trying again.",
)
otp_send_limiter = create_limiter(window_ms=15 * 60 * 1000, limit=3)
otp_verify_limiter = create_limiter(window_ms=15 * 60 * 1000, limit=5)
otp_email_cooldown_limiter = create_email_cooldown_limiter(cooldown_seconds=5.0)
email_resend_cooldown_limiter = create_email_cooldown_limiter(
    cooldown_seconds=30.0,
    message="Please wait 30 seconds before requesting another code.",
)
signup_limiter = create_limiter(
    window_ms=15 * 60 * 1000,
    limit=5,
    message="Too many sign-up attempts. Please try again later.",
)
change_password_limiter = create_limiter(
    window_ms=15 * 60 * 1000,
    limit=5,
    message="Too many password change attempts. Please try again later.",
)
delete_me_limiter = create_limiter(
    window_ms=15 * 60 * 1000,
    limit=3,
    message="Too many deletion attempts. Please try again later.",
)
