import httpx

from src.config import config
from src.util.logger import logger

ONESIGNAL_API_URL = "https://api.onesignal.com/notifications"


async def send_onesignal_notification(
    title: str,
    message: str,
    user_id: str | list[str] | None = None,
    segments: list[str] | None = None,
    subscription_ids: list[str] | None = None,
    data: dict | None = None,
    url: str | None = None,
) -> dict | None:
    """Send a push notification via OneSignal REST API.

    Adheres strictly to OneSignal official documentation:
    - Endpoint: POST https://api.onesignal.com/notifications
    - Auth: Authorization: Key <ONESIGNAL_REST_API_KEY>
    - Target: Exactly one of include_aliases (external_id), included_segments, or include_subscription_ids.
    """
    app_id = config.onesignal.app_id
    api_key = config.onesignal.rest_api_key

    if not app_id or not api_key:
        logger.warning(
            "OneSignal notification skipped: ONESIGNAL_APP_ID or ONESIGNAL_REST_API_KEY is not configured."
        )
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Key {api_key}",
    }

    payload: dict = {
        "app_id": app_id,
        "headings": {"en": title},
        "contents": {"en": message},
    }

    if data:
        payload["data"] = data
    if url:
        payload["url"] = url

    # Enforce OneSignal documentation rule: exactly ONE targeting method per request
    if user_id:
        target_ids = [user_id] if isinstance(user_id, str) else user_id
        payload["target_channel"] = "push"
        payload["include_aliases"] = {"external_id": target_ids}
    elif subscription_ids:
        payload["include_subscription_ids"] = subscription_ids
    else:
        # Default to segment targeting (e.g. Subscribed Users)
        payload["included_segments"] = segments or ["Subscribed Users"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                ONESIGNAL_API_URL, json=payload, headers=headers
            )
            res_data = response.json()

            if response.status_code == 200:
                notification_id = res_data.get("id")
                recipients = res_data.get("recipients", 0)
                logger.info(
                    f"OneSignal push sent successfully: id={notification_id}, recipients={recipients}"
                )
                return res_data
            else:
                logger.error(
                    f"OneSignal push failed (status {response.status_code}): {res_data}"
                )
                return None
    except Exception as exc:
        logger.error(f"Error dispatching OneSignal push notification: {exc}")
        return None
