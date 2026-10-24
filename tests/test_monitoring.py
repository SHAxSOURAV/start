from typing import cast

from sentry_sdk.types import Event, Hint

from src.error.api_error import ApiError
from src.util.monitoring import (
    filter_transactions,
    init_sentry,
    scrub_sensitive_data,
)


def test_init_sentry_disabled_in_non_production() -> None:
    """Verifies that Sentry refuses to initialize in development/test environment."""
    # Under test environment with empty or dev DSN, it must return False
    assert init_sentry() is False


def test_scrub_sensitive_headers_and_body() -> None:
    """Verifies that PII, passwords, and tokens are scrubbed from Sentry events."""
    event_dict = {
        "request": {
            "headers": {
                "Authorization": "Bearer sensitive_token_12345",
                "Content-Type": "application/json",
            },
            "data": {
                "email": "user@example.com",
                "password": "SuperSecretPassword123",
                "otp": "123456",
            },
        }
    }
    event = cast(Event, event_dict)
    hint = cast(Hint, {})
    scrubbed = scrub_sensitive_data(event, hint)
    assert scrubbed is not None

    req: dict = scrubbed.get("request", {})  # type: ignore[assignment]
    headers: dict = req.get("headers", {})
    assert headers["Authorization"] == "[FILTERED]"
    assert headers["Content-Type"] == "application/json"

    body: dict = req.get("data", {})
    assert body["password"] == "[FILTERED]"
    assert body["otp"] == "[FILTERED]"
    assert body["email"] == "user@example.com"


def test_noise_reduction_drops_4xx_errors() -> None:
    """Verifies that 4xx client errors (bad request, 404, 401) are dropped from Sentry."""
    client_error = ApiError(404, "User not found")
    hint = cast(Hint, {"exc_info": (ApiError, client_error, None)})
    event = cast(Event, {"request": {"url": "http://testserver/api/v1/user/123"}})

    # Must return None so 4xx errors don't consume Sentry quota
    assert scrub_sensitive_data(event, hint) is None


def test_filter_health_check_transactions() -> None:
    """Verifies that high-frequency health checks and docs are dropped from transactions."""
    health_event = cast(Event, {"request": {"url": "http://testserver/health/ready"}})
    assert filter_transactions(health_event, cast(Hint, {})) is None

    live_event = cast(Event, {"request": {"url": "http://testserver/health/live"}})
    assert filter_transactions(live_event, cast(Hint, {})) is None

    docs_event = cast(Event, {"request": {"url": "http://testserver/docs"}})
    assert filter_transactions(docs_event, cast(Hint, {})) is None

    # Legitimate business transactions must be kept
    api_event = cast(
        Event, {"request": {"url": "http://testserver/api/v1/payment/checkout"}}
    )
    assert filter_transactions(api_event, cast(Hint, {})) is not None
