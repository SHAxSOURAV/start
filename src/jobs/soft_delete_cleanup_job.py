from datetime import UTC, datetime, timedelta

from src.app.module.admin.admin_model import Admin
from src.app.module.auth.auth_model import Auth
from src.app.module.user.user_model import User
from src.util.logger import logger
from src.util.unlink_file import unlink_file


async def purge_expired_soft_deleted_accounts() -> None:
    """Permanently deletes accounts that were soft-deleted 30 or more days ago."""
    threshold = datetime.now(UTC) - timedelta(days=30)

    # Use compound index (isDeleted, deletedAt) for superfast IXSCAN
    cursor = Auth.get_pymongo_collection().find(
        {"isDeleted": True, "deletedAt": {"$lte": threshold}},
        {"_id": 1, "role": 1},
    )
    expired_auths = await cursor.to_list(length=100)
    if not expired_auths:
        return

    purged_count = 0
    for auth_doc in expired_auths:
        auth_id = auth_doc["_id"]

        user = await User.get_pymongo_collection().find_one({"authId": auth_id})
        if user:
            if user.get("profile_image"):
                unlink_file(user["profile_image"])
            await User.get_pymongo_collection().delete_one({"_id": user["_id"]})

        admin = await Admin.get_pymongo_collection().find_one({"authId": auth_id})
        if admin:
            if admin.get("profile_image"):
                unlink_file(admin["profile_image"])
            await Admin.get_pymongo_collection().delete_one({"_id": admin["_id"]})

        await Auth.get_pymongo_collection().delete_one({"_id": auth_id})
        purged_count += 1

    if purged_count > 0:
        logger.info(
            f"Permanently purged {purged_count} soft-deleted accounts (exceeded 30-day retention)."
        )
