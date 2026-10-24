import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "y": 31536000}


def parse_expiry(expire_time: str | int) -> int:
    """Convert a jsonwebtoken-style span ("15m", "30d", 3600) to seconds."""
    if isinstance(expire_time, int):
        return expire_time

    match = re.fullmatch(r"\s*(\d+)\s*([smhdwy])?\s*", expire_time, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid expiry format: {expire_time}")

    amount = int(match.group(1))
    unit = (match.group(2) or "s").lower()
    return amount * _UNITS[unit]


def create_token(payload: dict[str, Any], secret: str, expire_time: str | int) -> str:
    claims = {
        **payload,
        "jti": payload.get("jti") or str(uuid.uuid4()),
        "exp": datetime.now(UTC) + timedelta(seconds=parse_expiry(expire_time)),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def create_reset_token(
    payload: dict[str, Any], secret: str, expire_time: str | int
) -> str:
    claims = {
        **payload,
        "jti": payload.get("jti") or str(uuid.uuid4()),
        "exp": datetime.now(UTC) + timedelta(seconds=parse_expiry(expire_time)),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(claims, secret, algorithm="HS256")


def verify_token(token: str, secret: str) -> dict[str, Any]:
    return jwt.decode(token, secret, algorithms=["HS256"])


class jwt_helpers:  # noqa: N801 - kept as a namespace, as in the TypeScript source
    create_token = staticmethod(create_token)
    create_reset_token = staticmethod(create_reset_token)
    verify_token = staticmethod(verify_token)
