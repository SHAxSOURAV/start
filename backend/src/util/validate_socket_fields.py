from typing import Any

from src.socket.emit_error import emit_error
from src.util.http_status import status


async def validate_socket_fields(
    sid: str, payload: dict[str, Any] | None, required_fields: list[str]
) -> None:
    """Validates required fields in socket event payloads.

    Raises through emit_error as soon as a required field is missing.
    """
    if not payload:
        await emit_error(sid, status.BAD_REQUEST, "Request payload is required")

    for field in required_fields:
        value = (payload or {}).get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            await emit_error(sid, status.BAD_REQUEST, f"{field} is required")
