import re
from typing import Any

import socketio

from src.app.module.auth.auth_model import Auth
from src.config import config
from src.types.auth_types import AuthUserPayload
from src.util.jwt_helpers import jwt_helpers

BEARER = re.compile(r"^Bearer\s+", re.IGNORECASE)


async def socket_auth(
    environ: dict[str, Any], auth: dict[str, Any] | None
) -> AuthUserPayload:
    """Authenticates the handshake with the same JWT used by the REST API.

    The client must connect with `{ auth: { token } }`. Refusals surface on the
    client as a `connect_error` event.
    """
    token = (auth or {}).get("token")
    if not token:
        header = environ.get("HTTP_AUTHORIZATION")
        if header:
            token = BEARER.sub("", header)

    if not token:
        raise socketio.exceptions.ConnectionRefusedError(
            "Authentication token is required"
        )

    try:
        user = jwt_helpers.verify_token(token, config.jwt.secret)
    except Exception as error:
        raise socketio.exceptions.ConnectionRefusedError(
            "Invalid or expired token"
        ) from error

    auth_doc = await Auth.get(user["authId"])
    if not auth_doc:
        raise socketio.exceptions.ConnectionRefusedError("Account does not exist")
    if auth_doc.isBlocked:
        raise socketio.exceptions.ConnectionRefusedError("You are blocked")
    if not auth_doc.isActive:
        raise socketio.exceptions.ConnectionRefusedError("Account is not activated")

    return user  # type: ignore[return-value]
