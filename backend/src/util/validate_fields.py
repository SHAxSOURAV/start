from typing import Any

from src.error.api_error import ApiError
from src.util.http_status import status


def validate_fields(payload: dict[str, Any] | None, required_fields: list[str]) -> None:
    if not payload:
        raise ApiError(status.BAD_REQUEST, "Request body is required")

    for field in required_fields:
        if not payload.get(field):
            raise ApiError(status.BAD_REQUEST, f"{field} is required")
