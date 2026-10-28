from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from src.app.module.auth.auth_model import Auth
from src.app.module.subscription.subscription_model import Subscription
from src.app.module.user.user_model import User
from src.config import config
from src.error.api_error import ApiError
from src.util.base_document import utcnow
from src.util.enum import (
    EnumNotificationType,
    EnumSubscriptionStatus,
    EnumSubscriptionStore,
)
from src.util.http_status import status
from src.util.logger import error_logger, logger
from src.util.post_notification import post_notification


def _ms_to_datetime(ms: int | None) -> datetime | None:
    if ms is None:
        return None
    try:
        return datetime.fromtimestamp(ms / 1000.0, tz=UTC)
    except Exception:
        return None


async def _resolve_user_id(app_user_id: str, aliases: list[str]) -> ObjectId | None:
    """Finds MongoDB User ObjectId matching RevenueCat app_user_id or aliases."""
    candidates = [app_user_id] + (aliases or [])
    for candidate in candidates:
        if ObjectId.is_valid(candidate):
            oid = ObjectId(candidate)
            # Verify user exists in either User or Auth collection
            user_exists = await User.get_pymongo_collection().find_one({"_id": oid})
            if user_exists:
                return oid
            auth_exists = await Auth.get_pymongo_collection().find_one({"_id": oid})
            if auth_exists:
                return oid
    return None


async def handle_webhook(
    payload: dict[str, Any], authorization_header: str | None
) -> dict[str, Any]:
    """Processes inbound RevenueCat webhook lifecycle events.

    Gracefully bypassed when REVENUECAT_ENABLED is False.
    """
    # 1. Feature Flag Switch Check
    if not config.revenuecat.enabled:
        logger.info(
            "RevenueCat webhook received but REVENUECAT_ENABLED is False. Bypassing."
        )
        return {
            "status": "bypassed",
            "message": "RevenueCat integration is disabled via configuration.",
        }

    # 2. Authorization Header Security Check
    expected_secret = config.revenuecat.webhook_secret
    if expected_secret:
        if not authorization_header or (
            authorization_header != expected_secret
            and authorization_header != f"Bearer {expected_secret}"
        ):
            raise ApiError(status.UNAUTHORIZED, "Invalid webhook authorization secret")

    event = payload.get("event")
    if not isinstance(event, dict):
        raise ApiError(status.BAD_REQUEST, "Missing event object in payload")

    event_id = event.get("id")
    event_type = event.get("type", "UNKNOWN")
    app_user_id = event.get("app_user_id", "")
    aliases = event.get("aliases", [])
    product_id = event.get("product_id")
    entitlements = event.get("entitlement_ids") or []
    store = event.get("store") or EnumSubscriptionStore.UNKNOWN
    environment = event.get("environment", "SANDBOX")
    cancel_reason = event.get("cancel_reason")

    purchased_at = _ms_to_datetime(event.get("purchased_at_ms"))
    expires_at = _ms_to_datetime(event.get("expiration_at_ms"))

    logger.info(
        f"RevenueCat Webhook Event: {event_type} (id={event_id}) for user={app_user_id}"
    )

    user_oid = await _resolve_user_id(app_user_id, aliases)
    if not user_oid:
        logger.warning(
            f"RevenueCat user '{app_user_id}' could not be resolved to any MongoDB User."
        )
        return {"status": "user_unresolved", "eventId": event_id}

    # 3. Determine Subscription Status based on Event Type
    sub_status = EnumSubscriptionStatus.ACTIVE
    is_auto_renewing = True
    notification_title: str | None = None
    notification_body: str | None = None

    if event_type in ["INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION"]:
        sub_status = EnumSubscriptionStatus.ACTIVE
        is_auto_renewing = True
        if event_type == "INITIAL_PURCHASE":
            notification_title = "Subscription Activated 🎉"
            notification_body = (
                f"Welcome! Your {product_id or 'premium'} subscription is now active."
            )
        else:
            notification_title = "Subscription Renewed"
            notification_body = (
                f"Your {product_id or 'premium'} subscription was successfully renewed."
            )

    elif event_type == "CANCELLATION":
        # User turned off auto-renew; active until expires_at
        sub_status = EnumSubscriptionStatus.CANCELED
        is_auto_renewing = False
        notification_title = "Subscription Canceled"
        notification_body = (
            "Your subscription will remain active until the end of the billing period."
        )

    elif event_type == "EXPIRATION":
        sub_status = EnumSubscriptionStatus.EXPIRED
        is_auto_renewing = False
        notification_title = "Subscription Expired"
        notification_body = "Your subscription has expired. Renew today to continue enjoying premium benefits."

    elif event_type == "BILLING_ISSUE":
        sub_status = EnumSubscriptionStatus.BILLING_ISSUE
        notification_title = "Payment Alert ⚠️"
        notification_body = "There was an issue processing your renewal. Please update your payment method."

    # 4. Upsert Subscription State in MongoDB
    update_data: dict[str, Any] = {
        "userId": user_oid,
        "appUserId": app_user_id,
        "originalAppUserId": event.get("original_app_user_id"),
        "aliases": aliases,
        "status": sub_status,
        "productId": product_id,
        "entitlements": entitlements,
        "store": store,
        "environment": environment,
        "isAutoRenewing": is_auto_renewing,
        "cancelReason": cancel_reason,
        "rawEvent": event,
        "updatedAt": utcnow(),
    }
    if purchased_at:
        update_data["purchasedAt"] = purchased_at
    if expires_at:
        update_data["expiresAt"] = expires_at

    await Subscription.get_pymongo_collection().update_one(
        {"userId": user_oid},
        {"$set": update_data, "$setOnInsert": {"createdAt": utcnow()}},
        upsert=True,
    )

    # 5. Dispatch multi-channel notification to user if applicable
    if notification_title and notification_body:
        try:
            await post_notification(
                title=notification_title,
                message=notification_body,
                to_id=str(user_oid),
                notification_type=EnumNotificationType.PAYMENT,
                data={
                    "type": "subscription",
                    "status": sub_status,
                    "productId": product_id,
                },
            )
        except Exception as notif_err:
            error_logger.error(
                f"Failed to dispatch subscription notification: {notif_err}"
            )

    return {
        "status": "success",
        "eventId": event_id,
        "subscriptionStatus": sub_status,
        "userId": str(user_oid),
    }


async def get_my_subscription(user_id: str) -> dict[str, Any]:
    """Retrieves current subscription status and entitlements for authenticated user."""
    is_enabled = bool(config.revenuecat.enabled)
    sub = await Subscription.find_one({"userId": ObjectId(user_id)})

    if not sub:
        return {
            "enabled": is_enabled,
            "hasActiveSubscription": False,
            "status": EnumSubscriptionStatus.NONE,
            "entitlements": [],
            "planId": None,
            "expiresAt": None,
        }

    now = utcnow()
    is_active = sub.status in [
        EnumSubscriptionStatus.ACTIVE,
        EnumSubscriptionStatus.CANCELED,
    ] and (sub.expiresAt is None or sub.expiresAt > now)

    return {
        "enabled": is_enabled,
        "hasActiveSubscription": is_active,
        "status": sub.status,
        "planId": sub.productId,
        "entitlements": sub.entitlements,
        "store": sub.store,
        "isAutoRenewing": sub.isAutoRenewing,
        "purchasedAt": sub.purchasedAt.isoformat() if sub.purchasedAt else None,
        "expiresAt": sub.expiresAt.isoformat() if sub.expiresAt else None,
    }


async def check_user_entitlement(user_id: str, entitlement: str) -> dict[str, Any]:
    """Checks whether the user possesses an active entitlement (e.g. 'pro', 'premium')."""
    if not config.revenuecat.enabled:
        # If disabled in configuration, return false or grant based on system requirements
        return {
            "enabled": False,
            "hasAccess": False,
            "entitlement": entitlement,
            "message": "RevenueCat subscription system is currently disabled.",
        }

    sub = await Subscription.find_one({"userId": ObjectId(user_id)})
    if not sub:
        return {
            "enabled": True,
            "hasAccess": False,
            "entitlement": entitlement,
        }

    now = utcnow()
    has_access = (
        sub.status in [EnumSubscriptionStatus.ACTIVE, EnumSubscriptionStatus.CANCELED]
        and (sub.expiresAt is None or sub.expiresAt > now)
        and entitlement in sub.entitlements
    )

    return {
        "enabled": True,
        "hasAccess": has_access,
        "entitlement": entitlement,
        "expiresAt": sub.expiresAt.isoformat() if sub.expiresAt else None,
    }


class SubscriptionService:
    handle_webhook = staticmethod(handle_webhook)
    get_my_subscription = staticmethod(get_my_subscription)
    check_user_entitlement = staticmethod(check_user_entitlement)
