import asyncio
from typing import Any

from bson import ObjectId

from src.app.module.notification.admin_notification_model import AdminNotification
from src.app.module.notification.notification_model import Notification
from src.builder.query_builder import QueryBuilder, QueryParams
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.base_document import utcnow
from src.util.enum import EnumUserRole
from src.util.http_status import status
from src.util.validate_fields import validate_fields


async def get_notification(
    user_data: AuthUserPayload, query: dict[str, Any]
) -> dict[str, Any]:
    role = user_data["role"]
    if role != EnumUserRole.ADMIN:
        validate_fields(query, ["notificationId"])

    if role == EnumUserRole.ADMIN:
        notification = await AdminNotification.get_pymongo_collection().find_one({})
        if not notification:
            raise ApiError(status.NOT_FOUND, "Notification not found")
        return notification

    notification = await Notification.get_pymongo_collection().find_one(
        {"_id": ObjectId(str(query["notificationId"]))}
    )
    if not notification:
        raise ApiError(status.NOT_FOUND, "Notification not found")
    return notification


async def get_all_notifications(
    user_data: AuthUserPayload, query: QueryParams
) -> dict[str, Any]:
    """Admins read the AdminNotification feed; everyone else reads their own."""
    role = user_data["role"]
    user_id = user_data["userId"]

    if role == EnumUserRole.ADMIN:
        notification_query = (
            QueryBuilder(AdminNotification, {}, query)
            .search([])
            .filter()
            .sort()
            .paginate()
            .fields()
        )
    else:
        notification_query = (
            QueryBuilder(Notification, {"toId": ObjectId(str(user_id))}, query)
            .search([])
            .filter()
            .sort()
            .paginate()
            .fields()
        )

    notifications, meta = await asyncio.gather(
        notification_query.execute(), notification_query.count_total()
    )

    if notifications is None:
        raise ApiError(status.NOT_FOUND, "Notifications not found")

    return {"meta": meta, "notifications": notifications}


async def update_as_read_unread(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    role = user_data["role"]

    if role == EnumUserRole.ADMIN:
        result = await AdminNotification.get_pymongo_collection().update_many(
            {}, {"$set": {"isRead": payload.get("isRead"), "updatedAt": utcnow()}}
        )
    else:
        result = await Notification.get_pymongo_collection().update_many(
            {"toId": ObjectId(str(user_data["userId"]))},
            {"$set": {"isRead": payload.get("isRead"), "updatedAt": utcnow()}},
        )

    if not result.modified_count:
        raise ApiError(status.BAD_REQUEST, "Already updated")

    return {
        "acknowledged": result.acknowledged,
        "matchedCount": result.matched_count,
        "modifiedCount": result.modified_count,
    }


async def delete_notification(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    role = user_data["role"]
    validate_fields(payload, ["notificationId"])

    model = AdminNotification if role == EnumUserRole.ADMIN else Notification

    result = await model.get_pymongo_collection().find_one_and_delete(
        {"_id": ObjectId(str(payload["notificationId"]))}
    )
    if not result:
        raise ApiError(status.NOT_FOUND, "Notification not found")
    return result


class NotificationService:
    get_notification = staticmethod(get_notification)
    get_all_notifications = staticmethod(get_all_notifications)
    update_as_read_unread = staticmethod(update_as_read_unread)
    delete_notification = staticmethod(delete_notification)
