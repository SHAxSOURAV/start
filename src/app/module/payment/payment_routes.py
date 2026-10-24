from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.module.payment.payment_controller import PaymentController
from src.config import config

router = APIRouter()

router.add_api_route(
    "/config",
    PaymentController.get_public_config,
    methods=["GET"],
)

router.add_api_route(
    "/create-checkout-session",
    PaymentController.create_checkout_session,
    methods=["POST"],
    dependencies=[Depends(auth(config.auth_level.user))],
)

router.add_api_route(
    "/create-payment-intent",
    PaymentController.create_payment_intent,
    methods=["POST"],
    dependencies=[Depends(auth(config.auth_level.user))],
)

router.add_api_route(
    "/webhook",
    PaymentController.handle_webhook,
    methods=["POST"],
)

router.add_api_route(
    "/my-payments",
    PaymentController.get_my_payments,
    methods=["GET"],
    dependencies=[Depends(auth(config.auth_level.user))],
)
