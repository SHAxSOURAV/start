"""Enterprise Sentry APM & Crash Reporting Module.

Provides automated exception tracking, PII data scrubbing (passwords, tokens, OTPs),
health check transaction filtering, and environment gating (active only in production/staging).
"""

from __future__ import annotations

from typing import Any

from sentry_sdk.types import Event, Hint

from src.config import config
from src.util.logger import logger

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "new_password",
        "old_password",
        "confirm_password",
        "otp",
        "token",
        "access_token",
        "refresh_token",
        "authorization",
        "credit_card",
        "secret",
        "cvv",
        "api_key",
    }
)

IGNORED_TRANSACTION_PATHS: tuple[str, ...] = (
    "/health",
    "/health/live",
    "/health/ready",
    "/api/v1/health",
    "/metrics",
    "/docs",
    "/docs/openapi.json",
    "/favicon.ico",
)


def scrub_sensitive_data(event: Event, hint: Hint) -> Event | None:
    """Sanitizes PII and credentials, and drops 4xx client errors (Noise Reduction)."""
    # 1. Noise Reduction: Drop expected 4xx client errors from Sentry
    exc_info = hint.get("exc_info")
    if exc_info and len(exc_info) > 1 and exc_info[1] is not None:
        exc = exc_info[1]
        status_code = getattr(exc, "status_code", None) or getattr(
            exc, "statusCode", None
        )
        if isinstance(status_code, int) and 400 <= status_code < 500:
            return None

    request_data = event.get("request", {})

    # 2. Scrub sensitive request headers (e.g., Authorization: Bearer ...)
    if "headers" in request_data and isinstance(request_data["headers"], dict):
        for key in list(request_data["headers"].keys()):
            if key.lower() in SENSITIVE_KEYS:
                request_data["headers"][key] = "[FILTERED]"

    # 3. Scrub sensitive fields from JSON request body
    body_data = request_data.get("data")
    if isinstance(body_data, dict):
        for key in list(body_data.keys()):
            if key.lower() in SENSITIVE_KEYS:
                body_data[key] = "[FILTERED]"

    return event


def filter_transactions(event: Event, hint: Hint) -> Event | None:
    """Filters high-frequency health checks and docs to conserve Sentry transaction quota."""
    request_data = event.get("request") or {}
    url_str = str(request_data.get("url") or "") if isinstance(request_data, dict) else ""
    transaction_name = str(event.get("transaction") or "")

    for ignored in IGNORED_TRANSACTION_PATHS:
        if ignored in url_str or ignored == transaction_name:
            return None

    return event


def init_sentry() -> bool:
    """Initializes Sentry monitoring only in production/staging with valid SENTRY_DSN."""
    # Guard: Never initialize in development, test, or when DSN is absent
    if config.env not in ("production", "staging") or not config.sentry_dsn:
        logger.info(
            f"Sentry monitoring disabled (NODE_ENV='{config.env}', "
            f"DSN configured={bool(config.sentry_dsn)})"
        )
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.pymongo import PyMongoIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=config.sentry_dsn,
            environment=config.env,
            release="mount-fuji@1.0.0",
            # Quota preservation: sample 10% of transactions for performance tracing
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            # Security: Prevent automatic capture of raw personal data
            send_default_pii=False,
            # Custom security scrubbers and noise filters
            before_send=scrub_sensitive_data,
            before_send_transaction=filter_transactions,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
                RedisIntegration(),
                PyMongoIntegration(),
            ],
        )
        logger.info(
            f"Sentry APM & Crash Reporting initialized in '{config.env}' mode."
        )
        return True

    except Exception as exc:
        logger.error(f"Failed to initialize Sentry: {exc}")
        return False


def set_sentry_user(
    user_id: str, role: str | None = None, email: str | None = None
) -> None:
    """Attaches authenticated user context to active Sentry scope for crash debugging."""
    try:
        import sentry_sdk

        user_context: dict[str, Any] = {"id": user_id}
        if role:
            user_context["role"] = role
        if email:
            user_context["email"] = email
        sentry_sdk.set_user(user_context)
    except Exception:
        pass
