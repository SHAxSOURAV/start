from collections.abc import Awaitable, Callable

from fastapi import Request

from src.config import config
from src.connection.connect_redis import RedisService
from src.error.api_error import ApiError
from src.util.http_status import status
from src.util.jwt_helpers import jwt_helpers


def auth(
    roles: list[str], is_accessible: bool = True
) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        token_with_bearer = request.headers.get("authorization")

        if not token_with_bearer and not is_accessible:
            return
        if not token_with_bearer:
            raise ApiError(status.UNAUTHORIZED, "You are not authorized for this role")
        if not token_with_bearer.startswith("Bearer"):
            raise ApiError(status.UNAUTHORIZED, "Invalid token format")

        parts = token_with_bearer.split(" ")
        if len(parts) < 2:
            raise ApiError(status.UNAUTHORIZED, "Invalid token format")
        token = parts[1].strip()

        # Step 1: Zero-IO verification in CPU memory (< 0.1 ms)
        try:
            verify_user = jwt_helpers.verify_token(token, config.jwt.secret)
        except Exception:
            raise ApiError(status.UNAUTHORIZED, "Invalid or expired token") from None

        request.state.user = verify_user

        # Step 2: Role check from JWT payload claims (Zero-IO)
        if roles and verify_user.get("role") not in roles:
            raise ApiError(
                status.FORBIDDEN,
                "Access Forbidden: You do not have permission to perform this action",
            )

        # Step 3: Sub-millisecond revocation & instant-ban check via Redis (~ 0.5 ms)
        auth_id = verify_user.get("authId")
        if not auth_id:
            raise ApiError(status.UNAUTHORIZED, "Invalid token payload")

        is_token_revoked, is_user_banned = await RedisService.is_revoked(
            verify_user.get("jti"), auth_id
        )
        if is_token_revoked:
            raise ApiError(
                status.UNAUTHORIZED,
                "Session has been logged out or revoked. Please sign in again.",
            )
        if is_user_banned:
            raise ApiError(
                status.FORBIDDEN,
                "Access revoked or password changed. Please sign in again.",
            )

        # Step 4: Validate embedded status flags from rich JWT payload
        if verify_user.get("isBlocked"):
            raise ApiError(status.FORBIDDEN, "You are blocked. Contact support")
        if verify_user.get("isActive") is False:
            raise ApiError(status.FORBIDDEN, "Account is not activated")

    return dependency
