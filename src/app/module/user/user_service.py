from typing import Any

from fastapi import Request

from src.app.module.auth.auth_model import AUTH_PUBLIC_PROJECTION, Auth
from src.app.module.user.user_model import User
from src.connection.connect_redis import RedisService
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.base_document import utcnow
from src.util.delete_falsy_field import delete_falsy_field
from src.util.http_status import status
from src.util.media_storage import delete_media, upload_media
from src.util.request_body import get_body, get_files, get_user


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


async def update_profile(request: Request) -> dict[str, Any]:
    data = await get_body(request)
    user_data = get_user(request)
    assert user_data is not None
    user_id = user_data["userId"]
    auth_id = user_data["authId"]

    update_data: dict[str, Any] = {**data}
    files = get_files(request)

    delete_falsy_field(data)
    existing_user = await User.get_pymongo_collection().find_one({"_id": _oid(user_id)})

    has_new_image = False
    if files.get("profile_image"):
        local_path = files["profile_image"][0]["path"]
        update_data["profile_image"] = await upload_media(
            local_path, folder="profile_images", retention_category="profiles"
        )
        has_new_image = True

    if update_data.get("name") is not None:
        await Auth.get_pymongo_collection().update_one(
            {"_id": _oid(auth_id)},
            {"$set": {"name": update_data["name"], "updatedAt": utcnow()}},
        )
    auth = await Auth.get_pymongo_collection().find_one({"_id": _oid(auth_id)})

    user = await User.get_pymongo_collection().find_one_and_update(
        {"_id": _oid(user_id)},
        {"$set": {**update_data, "updatedAt": utcnow()}},
        return_document=True,
    )

    if not auth or not user:
        raise ApiError(status.NOT_FOUND, "User not found!")

    if has_new_image and existing_user and existing_user.get("profile_image"):
        await delete_media(existing_user["profile_image"])

    return await populate_auth(user)  # type: ignore[return-value]


async def get_profile(user_data: AuthUserPayload) -> dict[str, Any]:
    user_id = user_data["userId"]
    auth_id = user_data["authId"]

    auth = await Auth.get_pymongo_collection().find_one({"_id": _oid(auth_id)})
    result = await User.get_pymongo_collection().find_one({"_id": _oid(user_id)})

    if not auth or not result:
        raise ApiError(status.NOT_FOUND, "User not found")

    if auth.get("isBlocked"):
        raise ApiError(status.FORBIDDEN, "You are blocked. Contact support")

    return await populate_auth(result)  # type: ignore[return-value]


async def delete_my_account(payload: dict[str, Any]) -> None:
    email = payload.get("email")
    password = payload.get("password")

    auth = await Auth.get_pymongo_collection().find_one({"email": email})
    user = await User.get_pymongo_collection().find_one({"email": email})

    if not auth or not user:
        raise ApiError(status.NOT_FOUND, "User does not exist")

    if auth.get("password") and not await Auth.is_password_matched(
        password or "", auth["password"]
    ):
        raise ApiError(status.FORBIDDEN, "Password is incorrect")

    if user.get("profile_image"):
        await delete_media(user["profile_image"])

    await Auth.get_pymongo_collection().delete_one({"_id": auth["_id"]})
    await User.get_pymongo_collection().delete_one({"_id": user["_id"]})
    await RedisService.ban_user(auth["_id"], 900)


def _oid(value: Any) -> Any:
    from bson import ObjectId

    return ObjectId(str(value))


class UserService:
    get_profile = staticmethod(get_profile)
    delete_my_account = staticmethod(delete_my_account)
    update_profile = staticmethod(update_profile)
