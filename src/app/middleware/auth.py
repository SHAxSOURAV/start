from collections.abc import Awaitable, Callable

from fastapi import Request

from src.app.module.auth.auth_model import Auth
from src.config import config
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

        verify_user = jwt_helpers.verify_token(token, config.jwt.secret)
        request.state.user = verify_user

        is_exist = await Auth.get(verify_user["authId"])
        if not is_exist:
            raise ApiError(status.UNAUTHORIZED, "You are not authorized")
        if is_exist.isBlocked:
            raise ApiError(status.FORBIDDEN, "You are blocked. Contact support")
        if not is_exist.isActive:
            raise ApiError(status.FORBIDDEN, "Account is not activated")

        # Invalidate access tokens issued before password was changed
        if is_exist.passwordChangedAt:
            token_iat = verify_user.get("iat")
            if token_iat is not None and token_iat < int(
                is_exist.passwordChangedAt.timestamp()
            ):
                raise ApiError(
                    status.UNAUTHORIZED,
                    "Password was recently changed. Please log in again.",
                )

        if roles and verify_user["role"] not in roles:
            raise ApiError(
                status.FORBIDDEN,
                "Access Forbidden: You do not have permission to perform this action",
            )

    return dependency
