from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.module.subscription.subscription_controller import (
    SubscriptionController,
)
from src.config import config

router = APIRouter()

user_only = [Depends(auth(config.auth_level.user))]

# 1. Inbound Webhook from RevenueCat (Secret verified in service)
router.add_api_route(
    "/webhook",
    SubscriptionController.revenuecat_webhook,
    methods=["POST"],
)

# 2. Authenticated User Endpoints
router.add_api_route(
    "/my-subscription",
    SubscriptionController.get_my_subscription,
    methods=["GET"],
    dependencies=user_only,
)

router.add_api_route(
    "/check-entitlement",
    SubscriptionController.check_entitlement,
    methods=["GET"],
    dependencies=user_only,
)
