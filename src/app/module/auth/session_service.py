from datetime import UTC, datetime, timedelta
from typing import Any, cast

from beanie import PydanticObjectId

from src.app.module.admin.admin_model import Admin
from src.app.module.auth.auth_model import Auth
from src.app.module.auth.session_model import Session
from src.app.module.auth.session_utils import hash_token, parse_user_agent
from src.app.module.user.user_model import User
from src.config import config
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.email_helpers import EmailHelpers
from src.util.enum import EnumUserRole
from src.util.fire_and_forget import fire_and_forget
from src.util.http_status import status
from src.util.jwt_helpers import jwt_helpers, parse_expiry
from src.util.post_notification import post_notification

GRACE_PERIOD_SECONDS = 15.0


def _now() -> datetime:
    return datetime.now(UTC)


def _oid(value: Any) -> PydanticObjectId:
    return PydanticObjectId(str(value))


def _issue_tokens(
    payload: dict[str, Any], session_id: str | None = None
) -> dict[str, str]:
    token_payload = {**payload}
    if session_id:
        token_payload["sessionId"] = session_id

    tokens = {
        "accessToken": jwt_helpers.create_token(
            token_payload, config.jwt.secret, config.jwt.expires_in
        ),
        "refreshToken": jwt_helpers.create_token(
            token_payload, config.jwt.refresh_secret, config.jwt.refresh_expires_in
        ),
    }
    return tokens


async def _account_detail(auth: Auth) -> dict[str, Any] | None:
    if auth.role in (EnumUserRole.ADMIN, EnumUserRole.SUPER_ADMIN):
        return await Admin.get_pymongo_collection().find_one({"authId": auth.id})
    return await User.get_pymongo_collection().find_one({"authId": auth.id})


class SessionService:
    @staticmethod
    async def create_user_session(
        auth_id: Any,
        user_id: Any,
        ip: str,
        user_agent: str,
        base_payload: dict[str, Any],
    ) -> tuple[dict[str, str], Session]:
        """Creates a new tracked device session and generates the initial token pair."""
        now = _now()
        refresh_lifespan = timedelta(
            seconds=parse_expiry(config.jwt.refresh_expires_in)
        )
        expires_at = now + refresh_lifespan
        device_name = parse_user_agent(user_agent)
        auth_oid = _oid(auth_id)

        # Check if user has previous sessions and if this device is new
        existing_count = await Session.find({"authId": auth_oid}).count()
        existing_device = await Session.find_one(
            {"authId": auth_oid, "device": device_name}
        )
        is_new_device = existing_count > 0 and existing_device is None

        session = Session(
            authId=auth_oid,
            userId=_oid(user_id),
            refreshTokenHash="pending",
            device=device_name,
            ip=ip,
            userAgent=user_agent or "",
            isValid=True,
            expiresAt=expires_at,
            lastActiveAt=now,
        )
        await session.insert()

        tokens = _issue_tokens(base_payload, session_id=str(session.id))
        session.refreshTokenHash = hash_token(tokens["refreshToken"])
        await session.save()

        # If a new device is detected for an established user, send security alerts
        if is_new_device:
            user_email = base_payload.get("email")
            if user_email:
                fire_and_forget(
                    EmailHelpers.send_new_device_login_email(
                        user_email,
                        {
                            "name": user_email.split("@")[0],
                            "device": device_name,
                            "ip": ip,
                            "time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
                        },
                    )
                )
            fire_and_forget(
                post_notification(
                    title="Security Alert: New Sign-in",
                    message=f"New sign-in detected from {device_name} (IP: {ip}). If this was not you, please secure your account immediately.",
                    to_id=str(user_id),
                    data={"type": "security", "action": "new_device_login"},
                )
            )

        return tokens, session

    @staticmethod
    async def rotate_refresh_token(
        raw_refresh_token: str | None,
        ip: str,
        user_agent: str,
    ) -> tuple[dict[str, str], Session]:
        """Rotates refresh token with reuse detection and concurrent request grace period."""
        if not raw_refresh_token:
            raise ApiError(status.UNAUTHORIZED, "Refresh token is required")

        try:
            verified = cast(
                AuthUserPayload,
                jwt_helpers.verify_token(raw_refresh_token, config.jwt.refresh_secret),
            )
        except Exception as error:
            raise ApiError(status.UNAUTHORIZED, "Invalid refresh token") from error

        auth = await Auth.get(verified["authId"])
        if not auth:
            raise ApiError(status.UNAUTHORIZED, "Account does not exist")
        if getattr(auth, "isDeleted", False):
            raise ApiError(status.FORBIDDEN, "Account is deactivated")
        if not auth.isActive:
            raise ApiError(status.FORBIDDEN, "Account is not activated")
        if auth.isBlocked:
            raise ApiError(status.FORBIDDEN, "You are blocked. Contact support")

        # Invalidate if token was issued prior to password change
        if auth.passwordChangedAt:
            token_iat = verified.get("iat")
            if token_iat is not None and token_iat < int(
                auth.passwordChangedAt.timestamp()
            ):
                raise ApiError(
                    status.UNAUTHORIZED,
                    "Password was recently changed. Please log in again.",
                )

        current_token_hash = hash_token(raw_refresh_token)
        now = _now()

        # 1. Lookup session by current active refresh token hash
        session = await Session.find_one({"refreshTokenHash": current_token_hash})

        if not session:
            # Check if this token was recently rotated (Grace period or Theft detection)
            previous_session = await Session.find_one(
                {"previousTokenHash": current_token_hash}
            )

            if previous_session:
                rotated_at = previous_session.rotatedAt
                if rotated_at:
                    elapsed = (now - rotated_at).total_seconds()
                    if elapsed <= GRACE_PERIOD_SECONDS and previous_session.isValid:
                        # Allow race condition / concurrent requests within grace period
                        detail = await _account_detail(auth)
                        if not detail:
                            raise ApiError(status.NOT_FOUND, "Account detail not found")
                        token_payload = {
                            "authId": str(auth.id),
                            "userId": str(detail["_id"]),
                            "email": auth.email,
                            "role": auth.role,
                        }
                        # Re-issue current active tokens
                        new_tokens = _issue_tokens(
                            token_payload, session_id=str(previous_session.id)
                        )
                        return new_tokens, previous_session

                # Token theft detection: Token was reused after grace period expired!
                await Session.get_pymongo_collection().update_many(
                    {"authId": auth.id},
                    {"$set": {"isValid": False, "updatedAt": now}},
                )
                raise ApiError(
                    status.UNAUTHORIZED,
                    "Security alert: Stolen or reused refresh token detected. All sessions have been logged out.",
                )

            raise ApiError(
                status.UNAUTHORIZED, "Session expired or invalid. Please sign in again."
            )

        if not session.isValid:
            raise ApiError(
                status.UNAUTHORIZED,
                "This session has been revoked. Please sign in again.",
            )

        detail = await _account_detail(auth)
        if not detail:
            raise ApiError(status.NOT_FOUND, "Account detail not found")

        token_payload = {
            "authId": str(auth.id),
            "userId": str(detail["_id"]),
            "email": auth.email,
            "role": auth.role,
        }

        # Issue brand new rotated token pair
        new_tokens = _issue_tokens(token_payload, session_id=str(session.id))
        new_refresh_hash = hash_token(new_tokens["refreshToken"])

        refresh_lifespan = timedelta(
            seconds=parse_expiry(config.jwt.refresh_expires_in)
        )

        # Rotate session record
        session.previousTokenHash = current_token_hash
        session.refreshTokenHash = new_refresh_hash
        session.rotatedAt = now
        session.lastActiveAt = now
        session.expiresAt = now + refresh_lifespan
        session.ip = ip
        session.device = parse_user_agent(user_agent)
        await session.save()

        return new_tokens, session

    @staticmethod
    async def list_sessions(
        auth_id: Any, current_session_id: str | None = None
    ) -> list[dict[str, Any]]:
        """List all active, valid sessions for a given user."""
        sessions = (
            await Session.find({"authId": _oid(auth_id), "isValid": True})
            .sort("-lastActiveAt")
            .to_list()
        )

        return [
            {
                "sessionId": str(s.id),
                "device": s.device,
                "ip": s.ip,
                "lastActiveAt": s.lastActiveAt,
                "createdAt": s.createdAt,
                "isCurrent": str(s.id) == str(current_session_id)
                if current_session_id
                else False,
            }
            for s in sessions
        ]

    @staticmethod
    async def logout_current_session(
        raw_refresh_token: str | None, session_id: str | None = None
    ) -> None:
        """Revokes the current session using either token hash or sessionId."""
        now = _now()
        if session_id:
            await Session.get_pymongo_collection().update_one(
                {"_id": _oid(session_id)},
                {"$set": {"isValid": False, "updatedAt": now}},
            )
        elif raw_refresh_token:
            token_hash = hash_token(raw_refresh_token)
            await Session.get_pymongo_collection().update_one(
                {"refreshTokenHash": token_hash},
                {"$set": {"isValid": False, "updatedAt": now}},
            )

    @staticmethod
    async def revoke_single_session(auth_id: Any, target_session_id: str) -> None:
        """Remotely revokes a specific device session."""
        now = _now()
        result = await Session.get_pymongo_collection().update_one(
            {"_id": _oid(target_session_id), "authId": _oid(auth_id)},
            {"$set": {"isValid": False, "updatedAt": now}},
        )
        if result.matched_count == 0:
            raise ApiError(status.NOT_FOUND, "Session not found")

    @staticmethod
    async def logout_other_sessions(
        auth_id: Any, current_session_id: str | None
    ) -> int:
        """Revokes all active sessions for this user except the current one."""
        now = _now()
        query: dict[str, Any] = {"authId": _oid(auth_id), "isValid": True}
        if current_session_id:
            query["_id"] = {"$ne": _oid(current_session_id)}

        res = await Session.get_pymongo_collection().update_many(
            query,
            {"$set": {"isValid": False, "updatedAt": now}},
        )
        return int(res.modified_count)

    @staticmethod
    async def revoke_all_user_sessions(auth_id: Any) -> None:
        """Revokes all sessions (called on password change / reset)."""
        now = _now()
        await Session.get_pymongo_collection().update_many(
            {"authId": _oid(auth_id)},
            {"$set": {"isValid": False, "updatedAt": now}},
        )
