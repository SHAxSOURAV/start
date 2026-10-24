"""Production Stripe Payment Service.

Handles Stripe Checkout Sessions, PaymentIntents, Webhook lifecycle verification,
and automatic multi-channel push & in-app notifications upon payment events.
All synchronous Stripe network calls are executed in asyncio.to_thread to keep
the FastAPI event loop completely non-blocking.
"""

import asyncio
from typing import Any

import stripe
from bson import ObjectId

from src.app.module.auth.auth_model import Auth
from src.app.module.payment.payment_model import Payment
from src.app.module.payment.payment_validation import (
    CreateCheckoutSessionSchema,
    CreatePaymentIntentSchema,
)
from src.config import config
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.base_document import utcnow
from src.util.enum import EnumNotificationType, EnumPaymentStatus
from src.util.http_status import status
from src.util.logger import error_logger, logger
from src.util.post_notification import post_notification
from src.util.stripe_currency_validator import stripe_currency_validator


def _get_stripe_client() -> stripe.StripeClient:
    """Returns initialized StripeClient or raises ApiError if secret key is missing."""
    secret_key = config.stripe.stripe_secret_key
    if not secret_key or secret_key.startswith("sk_test_xxxx"):
        raise ApiError(
            status.SERVICE_UNAVAILABLE,
            "Stripe secret key is not properly configured in .env",
        )
    return stripe.StripeClient(secret_key)


def get_public_config() -> dict[str, Any]:
    """Returns publishable key and default currency for frontend Stripe Elements."""
    return {
        "publishableKey": config.stripe.publishable_key,
        "currency": config.stripe.currency,
        "isConfigured": bool(
            config.stripe.stripe_secret_key
            and not config.stripe.stripe_secret_key.startswith("sk_test_xxxx")
        ),
    }


async def create_checkout_session(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    """Creates a hosted Stripe Checkout Session for web or mobile redirect.

    Records a pending Payment document in MongoDB.
    """
    validated = CreateCheckoutSessionSchema(**payload)
    currency = validated.currency.lower()
    stripe_currency_validator(currency)

    user_id = user_data["userId"]
    auth_id = user_data["authId"]
    auth = await Auth.get_pymongo_collection().find_one({"_id": ObjectId(auth_id)})
    user_email = auth.get("email") if auth else None

    # Amount in smallest currency units (e.g. cents)
    unit_amount = int(round(validated.amount * 100))

    success_url = (
        validated.successUrl
        or config.stripe.success_url
        or f"{config.base_url}:{config.port}/api/v1/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = (
        validated.cancelUrl
        or config.stripe.cancel_url
        or f"{config.base_url}:{config.port}/api/v1/payment/cancel"
    )

    client = _get_stripe_client()

    def _sync_create_session() -> Any:
        session_params: Any = {
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": {
                            "name": validated.productName,
                            "description": validated.description or validated.productName,
                        },
                        "unit_amount": unit_amount,
                    },
                    "quantity": 1,
                }
            ],
            "mode": "payment",
            "customer_email": user_email,
            "client_reference_id": str(user_id),
            "metadata": {
                "userId": str(user_id),
                **{str(k): str(v) for k, v in validated.metadata.items()},
            },
            "success_url": success_url,
            "cancel_url": cancel_url,
        }
        return client.checkout.sessions.create(params=session_params)

    session = await asyncio.to_thread(_sync_create_session)

    payment = Payment(
        userId=ObjectId(user_id),
        userEmail=user_email,
        amount=validated.amount,
        currency=currency,
        status=EnumPaymentStatus.PENDING,
        stripeSessionId=session.id,
        description=validated.description or validated.productName,
        metadata=validated.metadata,
    )
    await payment.insert()

    return {
        "sessionId": session.id,
        "checkoutUrl": session.url,
        "paymentId": str(payment.id),
        "amount": validated.amount,
        "currency": currency,
    }


async def create_payment_intent(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    """Creates a Stripe PaymentIntent for custom in-app Stripe Elements checkout."""
    validated = CreatePaymentIntentSchema(**payload)
    currency = validated.currency.lower()
    stripe_currency_validator(currency)

    user_id = user_data["userId"]
    auth_id = user_data["authId"]
    auth = await Auth.get_pymongo_collection().find_one({"_id": ObjectId(auth_id)})
    user_email = auth.get("email") if auth else None

    unit_amount = int(round(validated.amount * 100))
    client = _get_stripe_client()

    def _sync_create_intent() -> Any:
        intent_params: Any = {
            "amount": unit_amount,
            "currency": currency,
            "automatic_payment_methods": {"enabled": True},
            "metadata": {
                "userId": str(user_id),
                **{str(k): str(v) for k, v in validated.metadata.items()},
            },
            "description": validated.description or "In-App Payment",
        }
        return client.payment_intents.create(params=intent_params)

    intent = await asyncio.to_thread(_sync_create_intent)

    payment = Payment(
        userId=ObjectId(user_id),
        userEmail=user_email,
        amount=validated.amount,
        currency=currency,
        status=EnumPaymentStatus.PENDING,
        stripePaymentIntentId=intent.id,
        description=validated.description,
        metadata=validated.metadata,
    )
    await payment.insert()

    return {
        "clientSecret": intent.client_secret,
        "paymentIntentId": intent.id,
        "paymentId": str(payment.id),
        "publishableKey": config.stripe.publishable_key,
        "amount": validated.amount,
        "currency": currency,
    }


async def handle_webhook(
    raw_payload: bytes, sig_header: str | None
) -> dict[str, Any]:
    """Verifies Stripe Webhook signature and processes asynchronous payment events.

    Dispatches OneSignal push + MongoDB in-app notifications on completion or failure.
    """
    webhook_secret = config.stripe.webhook_secret
    if not webhook_secret:
        logger.warning(
            "Stripe webhook received but STRIPE_WEBHOOK_SECRET is not configured in .env."
        )
        raise ApiError(
            status.SERVICE_UNAVAILABLE, "Stripe webhook secret is unconfigured"
        )

    if not sig_header:
        raise ApiError(status.BAD_REQUEST, "Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(
            raw_payload, sig_header, webhook_secret
        )
    except stripe.SignatureVerificationError as err:
        logger.warning(f"Stripe Webhook Signature Verification Failed: {err}")
        raise ApiError(status.BAD_REQUEST, "Invalid Stripe webhook signature") from err
    except Exception as exc:
        logger.error(f"Error parsing Stripe webhook payload: {exc}")
        raise ApiError(status.BAD_REQUEST, f"Webhook parse error: {exc}") from exc

    event_type = event.get("type", "UNKNOWN")
    event_id = event.get("id")
    data_object = event.get("data", {}).get("object", {})

    logger.info(f"Stripe Webhook Event Received: {event_type} (id={event_id})")

    # 1. Checkout Session Completed
    if event_type == "checkout.session.completed":
        session_id = data_object.get("id")
        payment_intent_id = data_object.get("payment_intent")
        customer_id = data_object.get("customer")
        amount_total = (data_object.get("amount_total") or 0) / 100.0
        currency = data_object.get("currency", "usd")
        client_ref_id = data_object.get("client_reference_id")

        query: dict[str, Any] = {"stripeSessionId": session_id}
        update_doc: dict[str, Any] = {
            "status": EnumPaymentStatus.SUCCEEDED,
            "stripePaymentIntentId": payment_intent_id,
            "stripeCustomerId": customer_id,
            "updatedAt": utcnow(),
        }

        payment = await Payment.get_pymongo_collection().find_one_and_update(
            query,
            {"$set": update_doc},
            return_document=True,
        )

        user_id_to_notify = str(payment["userId"]) if payment else client_ref_id

        if user_id_to_notify:
            try:
                await post_notification(
                    title="Payment Successful 🎉",
                    message=f"Your payment of {amount_total:.2f} {currency.upper()} has been received successfully.",
                    to_id=user_id_to_notify,
                    notification_type=EnumNotificationType.PAYMENT,
                    data={
                        "type": "payment",
                        "status": EnumPaymentStatus.SUCCEEDED,
                        "sessionId": session_id,
                    },
                )
            except Exception as notif_err:
                error_logger.error(f"Failed to dispatch payment notification: {notif_err}")

    # 2. PaymentIntent Succeeded (In-App Elements)
    elif event_type == "payment_intent.succeeded":
        intent_id = data_object.get("id")
        amount = (data_object.get("amount") or 0) / 100.0
        currency = data_object.get("currency", "usd")

        payment = await Payment.get_pymongo_collection().find_one_and_update(
            {"stripePaymentIntentId": intent_id},
            {
                "$set": {
                    "status": EnumPaymentStatus.SUCCEEDED,
                    "updatedAt": utcnow(),
                }
            },
            return_document=True,
        )

        if payment and payment.get("userId"):
            try:
                await post_notification(
                    title="Payment Succeeded 🎉",
                    message=f"Your payment of {amount:.2f} {currency.upper()} was completed.",
                    to_id=str(payment["userId"]),
                    notification_type=EnumNotificationType.PAYMENT,
                    data={"type": "payment", "intentId": intent_id},
                )
            except Exception as notif_err:
                error_logger.error(f"Failed to dispatch payment intent notification: {notif_err}")

    # 3. PaymentIntent Failed (Declined card / insufficient funds)
    elif event_type == "payment_intent.payment_failed":
        intent_id = data_object.get("id")
        last_error = data_object.get("last_payment_error", {})
        failure_msg = last_error.get("message", "Payment processing failed")

        payment = await Payment.get_pymongo_collection().find_one_and_update(
            {"stripePaymentIntentId": intent_id},
            {
                "$set": {
                    "status": EnumPaymentStatus.FAILED,
                    "failureReason": failure_msg,
                    "updatedAt": utcnow(),
                }
            },
            return_document=True,
        )

        if payment and payment.get("userId"):
            try:
                await post_notification(
                    title="Payment Failed ⚠️",
                    message=f"Your payment could not be processed: {failure_msg}",
                    to_id=str(payment["userId"]),
                    notification_type=EnumNotificationType.PAYMENT,
                    data={"type": "payment", "intentId": intent_id, "error": failure_msg},
                )
            except Exception as notif_err:
                error_logger.error(f"Failed to dispatch payment failure alert: {notif_err}")

    # 4. Charge Refunded
    elif event_type == "charge.refunded":
        payment_intent_id = data_object.get("payment_intent")
        payment = await Payment.get_pymongo_collection().find_one_and_update(
            {"stripePaymentIntentId": payment_intent_id},
            {
                "$set": {
                    "status": EnumPaymentStatus.REFUNDED,
                    "updatedAt": utcnow(),
                }
            },
            return_document=True,
        )

        if payment and payment.get("userId"):
            try:
                await post_notification(
                    title="Refund Processed",
                    message="A refund has been credited back to your original payment method.",
                    to_id=str(payment["userId"]),
                    notification_type=EnumNotificationType.PAYMENT,
                    data={"type": "payment", "status": EnumPaymentStatus.REFUNDED},
                )
            except Exception as notif_err:
                error_logger.error(f"Failed to dispatch refund notification: {notif_err}")

    return {"status": "success", "eventId": event_id, "eventType": event_type}


async def get_my_payments(
    user_data: AuthUserPayload, page: int = 1, limit: int = 10
) -> dict[str, Any]:
    """Retrieves paginated payment history for authenticated user."""
    user_id = ObjectId(user_data["userId"])
    skip = (page - 1) * limit

    col = Payment.get_pymongo_collection()
    cursor = col.find({"userId": user_id}).sort("createdAt", -1).skip(skip).limit(limit)
    payments = await cursor.to_list(length=limit)
    total = await col.count_documents({"userId": user_id})

    total_pages = (total + limit - 1) // limit if limit > 0 else 0

    return {
        "payments": payments,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPage": total_pages,
        },
    }


class PaymentService:
    get_public_config = staticmethod(get_public_config)
    create_checkout_session = staticmethod(create_checkout_session)
    create_payment_intent = staticmethod(create_payment_intent)
    handle_webhook = staticmethod(handle_webhook)
    get_my_payments = staticmethod(get_my_payments)
