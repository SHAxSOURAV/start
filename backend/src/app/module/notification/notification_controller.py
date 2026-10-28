from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.notification.notification_service import NotificationService
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_query, get_user
from src.util.send_response import send_response


@catch_async
async def get_notification(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await NotificationService.get_notification(user, get_query(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Notification retrieved successfully",
            "data": result,
        }
    )


@catch_async
async def get_all_notifications(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await NotificationService.get_all_notifications(user, get_query(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Notifications retrieved successfully",
            "meta": result["meta"],
            "data": result["notifications"],
        }
    )


@catch_async
async def get_unread_count(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await NotificationService.get_unread_count(user)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Unread notification count retrieved",
            "data": result,
        }
    )


@catch_async
async def mark_as_read(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await NotificationService.mark_as_read(user, await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Notifications marked as read",
            "data": result,
        }
    )


@catch_async
async def mark_all_as_read(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await NotificationService.mark_as_read(user, {"markAll": True})
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "All notifications marked as read",
            "data": result,
        }
    )


@catch_async
async def update_as_read_unread(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await NotificationService.update_as_read_unread(
        user, await get_body(request)
    )
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Notification status updated",
            "data": result,
        }
    )


@catch_async
async def delete_notification(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await NotificationService.delete_notification(
        user, await get_body(request)
    )
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Notification deleted successfully",
            "data": result,
        }
    )


@catch_async
async def clear_all_notifications(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await NotificationService.clear_all_notifications(user)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "All notifications cleared successfully",
            "data": result,
        }
    )


class NotificationController:
    get_notification = staticmethod(get_notification)
    get_all_notifications = staticmethod(get_all_notifications)
    get_unread_count = staticmethod(get_unread_count)
    mark_as_read = staticmethod(mark_as_read)
    mark_all_as_read = staticmethod(mark_all_as_read)
    update_as_read_unread = staticmethod(update_as_read_unread)
    delete_notification = staticmethod(delete_notification)
    clear_all_notifications = staticmethod(clear_all_notifications)
