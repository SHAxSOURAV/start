from src.app.module.notification.admin_notification_model import AdminNotification
from src.app.module.notification.notification_model import Notification
from src.util.fire_and_forget import fire_and_forget
from src.util.logger import logger
from src.util.onesignal import send_onesignal_notification


async def post_notification(
    title: str,
    message: str,
    to_id: str | None = None,
    data: dict | None = None,
    url: str | None = None,
    send_push: bool = True,
) -> None:
    if not title or not message:
        raise ValueError("Missing required fields: title, or message")

    try:
        if not to_id:
            await AdminNotification(title=title, message=message).insert()
        else:
            await Notification(toId=to_id, title=title, message=message).insert()

        # Asynchronously send OneSignal push notification without blocking
        if send_push:
            fire_and_forget(
                send_onesignal_notification(
                    title=title,
                    message=message,
                    user_id=to_id,
                    data=data,
                    url=url,
                )
            )
    except Exception as error:
        logger.error(f"Failed to post notification: {error}")
