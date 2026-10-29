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
    """Retrieve a single notification and mark it as read."""
    role = user_data["role"]
    validate_fields(query, ["notificationId"])
    notification_oid = ObjectId(str(query["notificationId"]))

    if role == EnumUserRole.ADMIN:
        notification = (
            await AdminNotification.get_pymongo_collection().find_one_and_update(
                {"_id": notification_oid},
                {"$set": {"isRead": True, "readAt": utcnow(), "updatedAt": utcnow()}},
                return_document=True,
            )
        )
        if not notification:
            raise ApiError(status.NOT_FOUND, "Notification not found")
        return notification

    notification = await Notification.get_pymongo_collection().find_one_and_update(
        {"_id": notification_oid, "toId": ObjectId(str(user_data["userId"]))},
        {"$set": {"isRead": True, "readAt": utcnow(), "updatedAt": utcnow()}},
        return_document=True,
    )
    if not notification:
        raise ApiError(status.NOT_FOUND, "Notification not found")
    return notification


async def get_all_notifications(
    user_data: AuthUserPayload, query: QueryParams
) -> dict[str, Any]:
    """Admins read AdminNotification feed; regular users read their personal feed."""
    role = user_data["role"]
    user_id = user_data["userId"]

    base_filter: dict[str, Any] = {}
    if role != EnumUserRole.ADMIN:
        base_filter["toId"] = ObjectId(str(user_id))

    # Optional filter by type or isRead
    if query.get("type"):
        base_filter["type"] = query["type"]
    if query.get("isRead") is not None:
        base_filter["isRead"] = str(query["isRead"]).lower() == "true"

    model = AdminNotification if role == EnumUserRole.ADMIN else Notification

    notification_query = (
        QueryBuilder(model, base_filter, query)
        .search(["title", "message"])
        .filter()
        .sort()
        .paginate()
        .fields()
    )

    # Compute unread count in parallel using index
    unread_filter = {**base_filter, "isRead": False}
    notifications, meta, unread_count = await asyncio.gather(
        notification_query.execute(),
        notification_query.count_total(),
        model.get_pymongo_collection().count_documents(unread_filter),
    )

    return {
        "meta": {**(meta or {}), "unreadCount": unread_count},
        "notifications": notifications or [],
    }


async def get_unread_count(user_data: AuthUserPayload) -> dict[str, int]:
    """Returns the unread notifications count for the active user badge."""
    role = user_data["role"]
    if role == EnumUserRole.ADMIN:
        count = await AdminNotification.get_pymongo_collection().count_documents(
            {"isRead": False}
        )
    else:
        count = await Notification.get_pymongo_collection().count_documents(
            {"toId": ObjectId(str(user_data["userId"])), "isRead": False}
        )
    return {"unreadCount": count}


async def mark_as_read(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    """Mark a single, multiple, or all notifications as read."""
    role = user_data["role"]
    user_id = user_data["userId"]
    model = AdminNotification if role == EnumUserRole.ADMIN else Notification

    filter_query: dict[str, Any] = {}
    if role != EnumUserRole.ADMIN:
        filter_query["toId"] = ObjectId(str(user_id))

    if payload.get("markAll"):
        filter_query["isRead"] = False
    elif payload.get("notificationIds"):
        filter_query["_id"] = {
            "$in": [ObjectId(str(nid)) for nid in payload["notificationIds"]]
        }
    elif payload.get("notificationId"):
        filter_query["_id"] = ObjectId(str(payload["notificationId"]))

    result = await model.get_pymongo_collection().update_many(
        filter_query,
        {
            "$set": {
                "isRead": True,
                "readAt": utcnow(),
                "updatedAt": utcnow(),
            }
        },
    )

    return {
        "matchedCount": result.matched_count,
        "modifiedCount": result.modified_count,
    }


async def update_as_read_unread(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    """Legacy backward-compatible toggle for marking all read/unread."""
    role = user_data["role"]
    is_read = bool(payload.get("isRead", True))
    model = AdminNotification if role == EnumUserRole.ADMIN else Notification

    filter_query: dict[str, Any] = {}
    if role != EnumUserRole.ADMIN:
        filter_query["toId"] = ObjectId(str(user_data["userId"]))

    update_doc: dict[str, Any] = {
        "isRead": is_read,
        "updatedAt": utcnow(),
    }
    if is_read:
        update_doc["readAt"] = utcnow()

    result = await model.get_pymongo_collection().update_many(
        filter_query, {"$set": update_doc}
    )

    return {
        "acknowledged": result.acknowledged,
        "matchedCount": result.matched_count,
        "modifiedCount": result.modified_count,
    }


async def delete_notification(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    """Delete a specific notification belonging to the active user."""
    role = user_data["role"]
    validate_fields(payload, ["notificationId"])

    model = AdminNotification if role == EnumUserRole.ADMIN else Notification
    query: dict[str, Any] = {"_id": ObjectId(str(payload["notificationId"]))}
    if role != EnumUserRole.ADMIN:
        query["toId"] = ObjectId(str(user_data["userId"]))

    result = await model.get_pymongo_collection().find_one_and_delete(query)
    if not result:
        raise ApiError(status.NOT_FOUND, "Notification not found")
    return result


async def clear_all_notifications(user_data: AuthUserPayload) -> dict[str, int]:
    """Clear all notifications for the active user."""
    role = user_data["role"]
    model = AdminNotification if role == EnumUserRole.ADMIN else Notification

    query: dict[str, Any] = {}
    if role != EnumUserRole.ADMIN:
        query["toId"] = ObjectId(str(user_data["userId"]))

    result = await model.get_pymongo_collection().delete_many(query)
    return {"deletedCount": result.deleted_count}


class NotificationService:
    get_notification = staticmethod(get_notification)
    get_all_notifications = staticmethod(get_all_notifications)
    get_unread_count = staticmethod(get_unread_count)
    mark_as_read = staticmethod(mark_as_read)
    update_as_read_unread = staticmethod(update_as_read_unread)
    delete_notification = staticmethod(delete_notification)
    clear_all_notifications = staticmethod(clear_all_notifications)
