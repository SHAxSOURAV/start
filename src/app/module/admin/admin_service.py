from typing import Any

from fastapi import Request

from src.app.module.admin.admin_model import Admin
from src.app.module.admin.admin_stats_service import (
    get_breakdowns_statistics,
    get_charts_statistics,
    get_overview_statistics,
)
from src.app.module.auth.auth_model import AUTH_PUBLIC_PROJECTION, Auth
from src.connection.connect_redis import RedisService
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.base_document import utcnow
from src.util.cloudinary import upload_file_to_cloudinary
from src.util.delete_falsy_field import delete_falsy_field
from src.util.enum import EnumUserRole
from src.util.http_status import status
from src.util.request_body import get_body, get_files, get_user
from src.util.unlink_file import unlink_file
from src.util.validate_fields import validate_fields


async def populate_auth(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    """`.populate("authId")` equivalent; the password is never included."""
    if not doc or not doc.get("authId"):
        return doc

    auth = await Auth.get_pymongo_collection().find_one(
        {"_id": doc["authId"]}, AUTH_PUBLIC_PROJECTION
    )
    if auth:
        doc["authId"] = auth
    return doc


async def create_admin(payload: dict[str, Any]) -> dict[str, Any]:
    validate_fields(payload, ["name", "email", "password"])

    name = payload["name"]
    email = payload["email"].strip().lower()
    password = payload["password"]

    existing = await Auth.find_one({"email": email})
    if existing:
        raise ApiError(status.CONFLICT, "An account with this email exists")

    # The insert hook hashes the password.
    # Admin accounts are created pre-activated -- no OTP flow.
    auth = Auth(
        name=name,
        email=email,
        password=password,
        role=EnumUserRole.ADMIN,
        isActive=True,
    )
    await auth.insert()

    admin = Admin(authId=auth.id, name=name, email=email)
    await admin.insert()

    return {"_id": admin.id, "name": name, "email": email, "role": auth.role}


async def update_profile(request: Request) -> dict[str, Any]:
    data = await get_body(request)
    user_data = get_user(request)
    assert user_data is not None
    user_id = user_data["userId"]
    auth_id = user_data["authId"]

    files = get_files(request)

    updated_data: dict[str, Any] = {}
    if data.get("address"):
        updated_data["address"] = data["address"]
    if data.get("phoneNumber"):
        updated_data["phoneNumber"] = data["phoneNumber"]
    if data.get("name"):
        updated_data["name"] = data["name"]

    delete_falsy_field(updated_data)
    existing_user = await Admin.get_pymongo_collection().find_one(
        {"_id": _oid(user_id)}
    )

    has_new_image = False
    if files.get("profile_image"):
        local_path = files["profile_image"][0]["path"]
        updated_data["profile_image"] = await upload_file_to_cloudinary(
            local_path, folder="admin_profiles"
        )
        has_new_image = True

    if updated_data.get("name") is not None:
        await Auth.get_pymongo_collection().update_one(
            {"_id": _oid(auth_id)},
            {"$set": {"name": updated_data["name"], "updatedAt": utcnow()}},
        )
    auth = await Auth.get_pymongo_collection().find_one({"_id": _oid(auth_id)})

    admin = await Admin.get_pymongo_collection().find_one_and_update(
        {"_id": _oid(user_id)},
        {"$set": {**updated_data, "updatedAt": utcnow()}},
        return_document=True,
    )

    if not auth or not admin:
        raise ApiError(status.NOT_FOUND, "User not found!")

    if has_new_image and existing_user and existing_user.get("profile_image"):
        unlink_file(existing_user["profile_image"])

    return await populate_auth(admin)  # type: ignore[return-value]


async def get_profile(user_data: AuthUserPayload) -> dict[str, Any]:
    user_id = user_data["userId"]
    auth_id = user_data["authId"]

    auth = await Auth.get_pymongo_collection().find_one({"_id": _oid(auth_id)})
    result = await Admin.get_pymongo_collection().find_one({"_id": _oid(user_id)})

    if not result or not auth:
        raise ApiError(status.NOT_FOUND, "Admin not found")
    if auth.get("isBlocked"):
        raise ApiError(status.FORBIDDEN, "You are blocked. Contact support")

    return await populate_auth(result)  # type: ignore[return-value]


async def delete_my_account(payload: dict[str, Any]) -> None:
    email = payload.get("email")
    password = payload.get("password")

    auth = await Auth.get_pymongo_collection().find_one({"email": email})
    admin = await Admin.get_pymongo_collection().find_one({"email": email})

    if not auth or not admin:
        raise ApiError(status.NOT_FOUND, "Admin does not exist")
    if auth.get("password") and not await Auth.is_password_matched(
        password or "", auth["password"]
    ):
        raise ApiError(status.FORBIDDEN, "Password is incorrect")

    if admin.get("profile_image"):
        unlink_file(admin["profile_image"])

    await Auth.get_pymongo_collection().delete_one({"_id": auth["_id"]})
    await Admin.get_pymongo_collection().delete_one({"_id": admin["_id"]})
    await RedisService.ban_user(auth["_id"], 900)


def _oid(value: Any) -> Any:
    from bson import ObjectId

    return ObjectId(str(value))


class AdminService:
    create_admin = staticmethod(create_admin)
    update_profile = staticmethod(update_profile)
    get_profile = staticmethod(get_profile)
    delete_my_account = staticmethod(delete_my_account)
    get_overview_statistics = staticmethod(get_overview_statistics)
    get_charts_statistics = staticmethod(get_charts_statistics)
    get_breakdowns_statistics = staticmethod(get_breakdowns_statistics)

