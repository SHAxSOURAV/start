from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from src.app.module.admin.admin_model import Admin
from src.app.module.auth.auth_model import (
    AUTH_PUBLIC_PROJECTION,
    Auth,
    hash_password,
)
from src.app.module.auth.oauth_service import (
    verify_apple_identity_token,
    verify_google_id_token,
)
from src.app.module.auth.session_service import SessionService
from src.app.module.user.user_model import User
from src.config import config
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.code_generator import code_generator
from src.util.email_helpers import EmailHelpers
from src.util.enum import EnumUserRole
from src.util.fire_and_forget import fire_and_forget
from src.util.http_status import status
from src.util.jwt_helpers import jwt_helpers
from src.util.validate_fields import validate_fields

MAX_OTP_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(UTC)


def _expiry(expired_at_ms: float) -> datetime:
    return datetime.fromtimestamp(expired_at_ms / 1000, tz=UTC)


def _minutes_left(expire: datetime) -> int:
    return round((expire.timestamp() * 1000 - _now().timestamp() * 1000) / (60 * 1000))


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def invalidate_activation_code(email: str) -> None:
    await Auth.get_pymongo_collection().update_one(
        {"email": email},
        {
            "$unset": {
                "activationCode": "",
                "activationCodeExpire": "",
                "activationAttempts": "",
            }
        },
    )


async def invalidate_verification_code(email: str) -> None:
    await Auth.get_pymongo_collection().update_one(
        {"email": email},
        {
            "$unset": {
                "isVerified": "",
                "verificationCode": "",
                "verificationCodeExpire": "",
                "verificationAttempts": "",
            }
        },
    )


async def registration_account(payload: dict[str, Any]) -> dict[str, Any]:
    validate_fields(payload, ["password", "confirmPassword", "email", "role", "name"])

    role = payload["role"]
    name = payload["name"]
    password = payload["password"]
    confirm_password = payload["confirmPassword"]
    email = payload["email"].strip().lower()

    activation_code, expired_at = code_generator(3)
    activation_code_expire = _expiry(expired_at)
    data = {
        "user": name,
        "activationCode": activation_code,
        "activationCodeExpire": _minutes_left(activation_code_expire),
    }

    # Only USER accounts may self-register. Admins are created by a
    # super admin (POST /admin/create-admin) or the seed script.
    if role not in [EnumUserRole.USER]:
        raise ApiError(status.BAD_REQUEST, "Invalid role")
    if password != confirm_password:
        raise ApiError(status.BAD_REQUEST, "Password and Confirm Password didn't match")

    user = await Auth.find_one({"email": email})
    if user:
        if getattr(user, "isDeleted", False):
            raise ApiError(
                status.BAD_REQUEST,
                "An account with this email is scheduled for deletion. Please sign in to restore your account or wait until the 30-day retention period expires.",
            )
        message = (
            "Account active. Please Login"
            if user.isActive
            else "Already have an account. Please activate"
        )

        if not user.isActive:
            user.activationCode = activation_code
            user.activationCodeExpire = activation_code_expire
            user.activationAttempts = 0
            await user.save()

            fire_and_forget(EmailHelpers.send_otp_resend_email(email, data))

        return {"isActive": user.isActive, "message": message}

    fire_and_forget(EmailHelpers.send_activation_email(email, data))

    auth = Auth(
        role=role,
        name=name,
        email=email,
        password=password,
        activationCode=activation_code,
        activationCodeExpire=activation_code_expire,
    )
    await auth.insert()

    await User(authId=auth.id, name=name, email=email).insert()

    return {
        "isActive": False,
        "message": "Account created successfully. Please check your email",
    }


async def resend_activation_code(payload: dict[str, Any]) -> None:
    email = payload["email"].strip().lower()

    user = await Auth.is_auth_exist(email)
    if not user:
        raise ApiError(status.BAD_REQUEST, "Email not found!")

    activation_code, expired_at = code_generator(3)
    activation_code_expire = _expiry(expired_at)
    data = {
        "user": user.name,
        "activationCode": activation_code,
        "activationCodeExpire": _minutes_left(activation_code_expire),
    }

    await Auth.get_pymongo_collection().update_one(
        {"_id": user.id},
        {
            "$set": {
                "activationCode": activation_code,
                "activationCodeExpire": activation_code_expire,
                "activationAttempts": 0,
                "updatedAt": _now(),
            }
        },
    )

    fire_and_forget(EmailHelpers.send_otp_resend_email(email, data))


async def _account_detail(auth: Auth) -> dict[str, Any] | None:
    if auth.role in (EnumUserRole.ADMIN, EnumUserRole.SUPER_ADMIN):
        return await Admin.get_pymongo_collection().find_one({"authId": auth.id})
    return await User.get_pymongo_collection().find_one({"authId": auth.id})


def _issue_tokens(payload: dict[str, Any], refresh: bool = True) -> dict[str, str]:
    tokens = {
        "accessToken": jwt_helpers.create_token(
            payload, config.jwt.secret, config.jwt.expires_in
        )
    }
    if refresh:
        tokens["refreshToken"] = jwt_helpers.create_token(
            payload, config.jwt.refresh_secret, config.jwt.refresh_expires_in
        )
    return tokens


async def activate_account(
    payload: dict[str, Any], ip: str = "unknown", user_agent: str = ""
) -> dict[str, Any]:
    activation_code = payload["activationCode"]
    email = payload["email"].strip().lower()

    auth = await Auth.find_one({"email": email})
    if not auth:
        raise ApiError(status.NOT_FOUND, "User not found")
    if not auth.activationCode:
        raise ApiError(
            status.NOT_FOUND,
            "Activation code not found. Get a new activation code",
        )
    expire = _aware(auth.activationCodeExpire)
    if not expire or expire < _now():
        raise ApiError(
            status.BAD_REQUEST,
            "Activation code expired. Get a new activation code",
        )
    if (auth.activationAttempts or 0) >= MAX_OTP_ATTEMPTS:
        await invalidate_activation_code(email)
        raise ApiError(
            status.TOO_MANY_REQUESTS,
            "Too many attempts. Get a new activation code",
        )
    if auth.activationCode != activation_code:
        await Auth.get_pymongo_collection().update_one(
            {"email": email}, {"$inc": {"activationAttempts": 1}}
        )
        raise ApiError(status.BAD_REQUEST, "Code didn't match!")

    await Auth.get_pymongo_collection().update_one(
        {"email": email},
        {
            "$set": {"isActive": True, "updatedAt": _now()},
            "$unset": {
                "activationCode": "",
                "activationCodeExpire": "",
                "activationAttempts": "",
            },
        },
    )

    result = await _account_detail(auth)
    if not result:
        raise ApiError(status.NOT_FOUND, "Account detail not found")

    token_payload = {
        "authId": str(auth.id),
        "userId": str(result["_id"]),
        "email": email,
        "role": auth.role,
    }

    tokens, session = await SessionService.create_user_session(
        auth.id, result["_id"], ip=ip, user_agent=user_agent, base_payload=token_payload
    )
    return {**tokens, "sessionId": str(session.id)}


async def login_account(
    payload: dict[str, Any], ip: str = "unknown", user_agent: str = ""
) -> dict[str, Any]:
    email = payload["email"].strip().lower()
    password = payload["password"]
    now = _now()

    auth = await Auth.is_auth_exist(email)

    # 1. Check if account is temporarily locked
    if auth and auth.lockUntil:
        lock_until = _aware(auth.lockUntil)
        if lock_until and lock_until > now:
            remaining_seconds = int((lock_until - now).total_seconds())
            remaining_minutes = max(1, (remaining_seconds + 59) // 60)
            raise ApiError(
                status.FORBIDDEN,
                f"Account is temporarily locked due to multiple failed login attempts. Please try again after {remaining_minutes} minute(s) or reset your password.",
            )

    # 2. Check password validity
    is_password_valid = False
    if auth and auth.password:
        is_password_valid = await Auth.is_password_matched(password, auth.password)

    if not auth:
        raise ApiError(status.UNAUTHORIZED, "Invalid email or password")

    if not is_password_valid:
        failed_count = (auth.failedLoginAttempts or 0) + 1
        if failed_count >= 5:
            lock_until_time = now + timedelta(minutes=15)
            await Auth.get_pymongo_collection().update_one(
                {"_id": auth.id},
                {
                    "$set": {
                        "failedLoginAttempts": failed_count,
                        "lockUntil": lock_until_time,
                        "updatedAt": now,
                    }
                },
            )
            raise ApiError(
                status.FORBIDDEN,
                "Account has been temporarily locked for 15 minutes due to 5 consecutive failed login attempts. You can also reset your password to regain access.",
            )
        else:
            await Auth.get_pymongo_collection().update_one(
                {"_id": auth.id},
                {
                    "$set": {
                        "failedLoginAttempts": failed_count,
                        "updatedAt": now,
                    }
                },
            )
            remaining_attempts = 5 - failed_count
            raise ApiError(
                status.UNAUTHORIZED,
                f"Invalid email or password. You have {remaining_attempts} attempt(s) remaining before your account is temporarily locked.",
            )

    # 3. Successful password match - reset failed attempts and unlock state
    if (auth.failedLoginAttempts or 0) > 0 or auth.lockUntil is not None:
        await Auth.get_pymongo_collection().update_one(
            {"_id": auth.id},
            {
                "$set": {
                    "failedLoginAttempts": 0,
                    "lockUntil": None,
                    "updatedAt": now,
                }
            },
        )

    if auth.isBlocked:
        raise ApiError(status.FORBIDDEN, "You are blocked. Contact support")

    was_soft_deleted = bool(getattr(auth, "isDeleted", False))
    if was_soft_deleted:
        # Signing in cancels the scheduled 30-day deletion and reactivates account
        now = _now()
        await Auth.get_pymongo_collection().update_one(
            {"_id": auth.id},
            {
                "$set": {
                    "isDeleted": False,
                    "deletedAt": None,
                    "isActive": True,
                    "updatedAt": now,
                }
            },
        )
        await User.get_pymongo_collection().update_one(
            {"authId": auth.id},
            {"$set": {"isDeleted": False, "deletedAt": None, "updatedAt": now}},
        )
        await Admin.get_pymongo_collection().update_one(
            {"authId": auth.id},
            {"$set": {"isDeleted": False, "deletedAt": None, "updatedAt": now}},
        )
    elif not auth.isActive:
        raise ApiError(
            status.BAD_REQUEST, "Please activate your account then try to login"
        )

    result = await _account_detail(auth)
    if not result:
        raise ApiError(status.NOT_FOUND, "Account detail not found")

    token_payload = {
        "authId": str(auth.id),
        "userId": str(result["_id"]),
        "email": email,
        "role": auth.role,
    }

    tokens, session = await SessionService.create_user_session(
        auth.id, result["_id"], ip=ip, user_agent=user_agent, base_payload=token_payload
    )
    return {
        **tokens,
        "sessionId": str(session.id),
        "isSoftDeleted": was_soft_deleted,
    }


async def _handle_social_login(
    provider: Literal["google", "apple"],
    profile: dict[str, Any],
    ip: str = "unknown",
    user_agent: str = "",
) -> dict[str, Any]:
    email = profile["email"].strip().lower()
    name = profile.get("name") or email.split("@")[0]
    picture = profile.get("picture")
    google_id = profile.get("googleId")
    apple_id = profile.get("appleId")

    auth = await Auth.find_one({"email": email})
    was_soft_deleted = False

    if auth:
        # Existing account (manual signup or previous social login)
        if auth.isBlocked:
            raise ApiError(status.FORBIDDEN, "You are blocked. Contact support")

        was_soft_deleted = bool(getattr(auth, "isDeleted", False))
        now = _now()
        set_fields: dict[str, Any] = {"updatedAt": now}

        if was_soft_deleted:
            set_fields["isDeleted"] = False
            set_fields["deletedAt"] = None
            set_fields["isActive"] = True

        # Social auth validates email ownership: activate if previously pending OTP
        if not auth.isActive:
            set_fields["isActive"] = True
        if not auth.isVerified:
            set_fields["isVerified"] = True

        # Link provider IDs if not recorded
        if provider == "google" and not auth.googleId:
            set_fields["googleId"] = google_id
        elif provider == "apple" and not auth.appleId:
            set_fields["appleId"] = apple_id

        await Auth.get_pymongo_collection().update_one(
            {"_id": auth.id},
            {"$set": set_fields},
        )

        if was_soft_deleted:
            await User.get_pymongo_collection().update_one(
                {"authId": auth.id},
                {"$set": {"isDeleted": False, "deletedAt": None, "updatedAt": now}},
            )
            await Admin.get_pymongo_collection().update_one(
                {"authId": auth.id},
                {"$set": {"isDeleted": False, "deletedAt": None, "updatedAt": now}},
            )

        if picture:
            await User.get_pymongo_collection().update_one(
                {"authId": auth.id, "profile_image": {"$in": [None, ""]}},
                {"$set": {"profile_image": picture, "updatedAt": now}},
            )

        detail = await _account_detail(auth)
        if not detail:
            user_doc = User(
                authId=auth.id, name=auth.name, email=email, profile_image=picture
            )
            await user_doc.insert()
            detail = await _account_detail(auth)
    else:
        # Brand new account registration via OAuth
        auth = Auth(
            name=name,
            email=email,
            password="",
            role=EnumUserRole.USER,
            isActive=True,
            isVerified=True,
            isDeleted=False,
            googleId=google_id,
            appleId=apple_id,
        )
        await auth.insert()

        user_doc = User(
            authId=auth.id,
            name=name,
            email=email,
            profile_image=picture,
        )
        await user_doc.insert()
        detail = await _account_detail(auth)

    if not detail:
        raise ApiError(status.NOT_FOUND, "Account detail not found")

    token_payload = {
        "authId": str(auth.id),
        "userId": str(detail["_id"]),
        "email": email,
        "role": auth.role,
    }
    tokens, session = await SessionService.create_user_session(
        auth.id, detail["_id"], ip=ip, user_agent=user_agent, base_payload=token_payload
    )

    return {
        **tokens,
        "sessionId": str(session.id),
        "isSoftDeleted": was_soft_deleted,
    }


async def google_sign_in(
    payload: dict[str, Any], ip: str = "unknown", user_agent: str = ""
) -> dict[str, Any]:
    id_token = payload.get("idToken")
    if not id_token:
        raise ApiError(status.BAD_REQUEST, "idToken is required")

    profile = await verify_google_id_token(id_token)
    return await _handle_social_login("google", profile, ip=ip, user_agent=user_agent)


async def apple_sign_in(
    payload: dict[str, Any], ip: str = "unknown", user_agent: str = ""
) -> dict[str, Any]:
    identity_token = payload.get("identityToken")
    if not identity_token:
        raise ApiError(status.BAD_REQUEST, "identityToken is required")

    profile = await verify_apple_identity_token(identity_token)

    # Apple only shares the user's name during the very first authorization
    client_name = payload.get("name")
    if client_name and not profile.get("name"):
        profile["name"] = client_name

    return await _handle_social_login("apple", profile, ip=ip, user_agent=user_agent)


async def forgot_pass(payload: dict[str, Any]) -> None:
    raw_email = payload.get("email")

    if not raw_email:
        raise ApiError(status.BAD_REQUEST, "Missing email")
    email = raw_email.strip().lower()

    user = await Auth.is_auth_exist(email)
    if not user:
        raise ApiError(status.BAD_REQUEST, "User not found!")

    activation_code, expired_at = code_generator(3)
    activation_code_expire = _expiry(expired_at)

    await Auth.get_pymongo_collection().update_one(
        {"_id": user.id},
        {
            "$set": {
                "verificationCode": activation_code,
                "verificationCodeExpire": activation_code_expire,
                "verificationAttempts": 0,
                "updatedAt": _now(),
            }
        },
    )

    data = {
        "user": user.name,
        "verificationCode": activation_code,
        "verificationCodeExpire": _minutes_left(activation_code_expire),
    }

    fire_and_forget(EmailHelpers.send_reset_password_email(email, data))


async def forget_pass_otp_verify(payload: dict[str, Any]) -> Any:
    raw_email = payload.get("email")
    code = payload.get("code")

    if not raw_email:
        raise ApiError(status.BAD_REQUEST, "Missing email")
    email = raw_email.strip().lower()

    auth = await Auth.find_one({"email": email})
    if not auth:
        raise ApiError(status.NOT_FOUND, "Account does not exist!")
    if not auth.verificationCode:
        raise ApiError(
            status.NOT_FOUND,
            "No verification code. Get a new verification code",
        )
    expire = _aware(auth.verificationCodeExpire)
    if not expire or expire < _now():
        raise ApiError(
            status.BAD_REQUEST,
            "Verification code expired. Get a new verification code",
        )
    if (auth.verificationAttempts or 0) >= MAX_OTP_ATTEMPTS:
        await invalidate_verification_code(email)
        raise ApiError(
            status.TOO_MANY_REQUESTS,
            "Too many attempts. Get a new verification code",
        )
    if auth.verificationCode != code:
        await Auth.get_pymongo_collection().update_one(
            {"email": email}, {"$inc": {"verificationAttempts": 1}}
        )
        raise ApiError(status.BAD_REQUEST, "Invalid verification code!")

    await Auth.get_pymongo_collection().update_one(
        {"email": auth.email},
        {
            "$set": {"isVerified": True, "updatedAt": _now()},
            "$unset": {"verificationCode": "", "verificationAttempts": ""},
        },
    )


async def reset_password(payload: dict[str, Any]) -> Any:
    email = payload["email"].strip().lower()
    new_password = payload["newPassword"]
    confirm_password = payload["confirmPassword"]

    if new_password != confirm_password:
        raise ApiError(status.BAD_REQUEST, "Passwords do not match")

    auth = await Auth.is_auth_exist(email)
    if not auth:
        raise ApiError(status.NOT_FOUND, "User not found!")
    if not auth.isVerified:
        raise ApiError(status.FORBIDDEN, "Please complete OTP verification")

    hashed_password = hash_pass(new_password)
    now = _now()

    await Auth.get_pymongo_collection().update_one(
        {"email": email},
        {
            "$set": {
                "password": hashed_password,
                "passwordChangedAt": now,
                "failedLoginAttempts": 0,
                "lockUntil": None,
                "updatedAt": now,
            },
            "$unset": {
                "isVerified": "",
                "verificationCode": "",
                "verificationCodeExpire": "",
                "verificationAttempts": "",
            },
        },
    )

    # Invalidate all active sessions across devices
    await SessionService.revoke_all_user_sessions(auth.id)


async def refresh_token(
    token: str | None, ip: str = "unknown", user_agent: str = ""
) -> dict[str, str]:
    new_tokens, session = await SessionService.rotate_refresh_token(
        token, ip, user_agent
    )
    return {
        **new_tokens,
        "sessionId": str(session.id),
    }


async def change_password(user_data: AuthUserPayload, payload: dict[str, Any]) -> None:
    email = user_data["email"].strip().lower()

    validate_fields(payload, ["oldPassword", "newPassword", "confirmPassword"])

    old_password = payload["oldPassword"]
    new_password = payload["newPassword"]
    confirm_password = payload["confirmPassword"]

    if new_password != confirm_password:
        raise ApiError(status.BAD_REQUEST, "Password and confirm password do not match")

    is_user_exist = await Auth.is_auth_exist(email)

    if not is_user_exist:
        raise ApiError(status.NOT_FOUND, "Account does not exist!")
    if is_user_exist.password and not await Auth.is_password_matched(
        old_password, is_user_exist.password
    ):
        raise ApiError(status.BAD_REQUEST, "Old password is incorrect")

    hashed_password = hash_pass(new_password)
    now = _now()

    await Auth.get_pymongo_collection().update_one(
        {"email": email},
        {
            "$set": {
                "password": hashed_password,
                "passwordChangedAt": now,
                "failedLoginAttempts": 0,
                "lockUntil": None,
                "updatedAt": now,
            }
        },
    )

    # Invalidate all active sessions across devices
    await SessionService.revoke_all_user_sessions(is_user_exist.id)


def _oid(value: Any) -> Any:
    from bson import ObjectId

    return ObjectId(str(value))


async def get_me(user_data: AuthUserPayload) -> dict[str, Any]:
    auth_id = user_data["authId"]

    # Use projection and index to fetch without password
    auth = await Auth.get_pymongo_collection().find_one(
        {"_id": _oid(auth_id), "isDeleted": {"$ne": True}},
        AUTH_PUBLIC_PROJECTION,
    )
    if not auth:
        raise ApiError(status.NOT_FOUND, "User not found")
    if auth.get("isBlocked"):
        raise ApiError(status.FORBIDDEN, "You are blocked. Contact support")

    role = auth.get("role")
    profile: dict[str, Any] | None = None
    if role in (EnumUserRole.ADMIN, EnumUserRole.SUPER_ADMIN):
        profile = await Admin.get_pymongo_collection().find_one(
            {"authId": _oid(auth_id)}
        )
    else:
        profile = await User.get_pymongo_collection().find_one(
            {"authId": _oid(auth_id)}
        )

    return {
        **auth,
        "profile": profile,
    }


async def delete_me(user_data: AuthUserPayload, payload: dict[str, Any]) -> None:
    auth_id = user_data["authId"]
    password = payload.get("password")

    if not password:
        raise ApiError(status.BAD_REQUEST, "Password is required to delete account")

    auth = await Auth.get_pymongo_collection().find_one({"_id": _oid(auth_id)})
    if not auth or auth.get("isDeleted"):
        raise ApiError(status.NOT_FOUND, "Account does not exist")

    if auth.get("password") and not await Auth.is_password_matched(
        password, auth["password"]
    ):
        raise ApiError(status.BAD_REQUEST, "Password is incorrect")

    now = _now()
    # 30-day soft delete: mark isDeleted=True, deletedAt=now, and deactivate account
    await Auth.get_pymongo_collection().update_one(
        {"_id": auth["_id"]},
        {
            "$set": {
                "isDeleted": True,
                "deletedAt": now,
                "isActive": False,
                "updatedAt": now,
            }
        },
    )
    await User.get_pymongo_collection().update_one(
        {"authId": auth["_id"]},
        {"$set": {"isDeleted": True, "deletedAt": now, "updatedAt": now}},
    )
    await Admin.get_pymongo_collection().update_one(
        {"authId": auth["_id"]},
        {"$set": {"isDeleted": True, "deletedAt": now, "updatedAt": now}},
    )

    # Invalidate all active sessions for deleted user
    await SessionService.revoke_all_user_sessions(auth["_id"])


def hash_pass(new_password: str) -> str:
    return hash_password(new_password)


class AuthService:
    get_me = staticmethod(get_me)
    delete_me = staticmethod(delete_me)
    registration_account = staticmethod(registration_account)
    login_account = staticmethod(login_account)
    google_sign_in = staticmethod(google_sign_in)
    apple_sign_in = staticmethod(apple_sign_in)
    change_password = staticmethod(change_password)
    forgot_pass = staticmethod(forgot_pass)
    reset_password = staticmethod(reset_password)
    activate_account = staticmethod(activate_account)
    forget_pass_otp_verify = staticmethod(forget_pass_otp_verify)
    resend_activation_code = staticmethod(resend_activation_code)
    refresh_token = staticmethod(refresh_token)
    list_sessions = staticmethod(SessionService.list_sessions)
    logout_current_session = staticmethod(SessionService.logout_current_session)
    revoke_single_session = staticmethod(SessionService.revoke_single_session)
    logout_other_sessions = staticmethod(SessionService.logout_other_sessions)
