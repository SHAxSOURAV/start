from typing import Any

from bson import ObjectId

from src.app.module.notification.admin_notification_model import AdminNotification
from src.app.module.notification.notification_model import Notification
from src.connection.socket_server import sio
from src.util.enum import EnumNotificationType, EnumSocketEvent
from src.util.fire_and_forget import fire_and_forget
from src.util.logger import logger
from src.util.onesignal import send_onesignal_notification


async def post_notification(
    title: str,
    message: str,
    to_id: str | None = None,
    sender_id: str | None = None,
    notification_type: str = EnumNotificationType.SYSTEM,
    data: dict[str, Any] | None = None,
    url: str | None = None,
    image: str | None = None,
    send_push: bool = True,
    emit_socket: bool = True,
) -> Notification | AdminNotification | None:
    """Universal notification dispatcher for the entire backend.

    Executes a 3-pillar notification workflow:
    1. Persists to MongoDB In-App feed with automatic 30-day TTL expiration.
    2. Emits a live WebSocket event to the recipient's personal room via Socket.IO.
    3. Asynchronously triggers a OneSignal push notification to registered devices via fire_and_forget.
    """
    if not title or not message:
        raise ValueError("Missing required fields: title or message")

    try:
        # 1. MongoDB In-App Feed Persistence (Protected by 30-day TTL index)
        created_doc: Notification | AdminNotification
        if not to_id:
            created_doc = await AdminNotification(
                title=title,
                message=message,
                type=notification_type,
                data=data or {},
                link=url,
                image=image,
            ).insert()
        else:
            created_doc = await Notification(
                toId=ObjectId(str(to_id)),
                senderId=ObjectId(str(sender_id)) if sender_id else None,
                title=title,
                message=message,
                type=notification_type,
                data=data or {},
                link=url,
                image=image,
            ).insert()

        notification_payload = {
            "id": str(created_doc.id),
            "title": title,
            "message": message,
            "type": notification_type,
            "data": data or {},
            "link": url,
            "image": image,
            "isRead": False,
            "createdAt": created_doc.createdAt.isoformat(),
        }

        # 2. Real-Time Socket.IO Emit (Instant badge/feed update for active clients)
        if emit_socket:
            try:
                target_room = str(to_id) if to_id else "admin"
                await sio.emit(
                    EnumSocketEvent.NOTIFICATION,
                    notification_payload,
                    room=target_room,
                )
            except Exception as sock_err:
                logger.warning(f"Socket.IO live notification emit failed: {sock_err}")

        # 3. Asynchronous OneSignal Mobile/Web Push (Non-blocking external HTTP)
        if send_push:
            push_data = {**(data or {}), "type": notification_type}
            fire_and_forget(
                send_onesignal_notification(
                    title=title,
                    message=message,
                    user_id=to_id,
                    segments=None if to_id else ["Admins"],
                    data=push_data,
                    url=url,
                )
            )

        return created_doc

    except Exception as error:
        logger.error(f"Failed to post notification: {error}")
        return None
