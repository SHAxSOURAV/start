from typing import Any

from fastapi import APIRouter

from src.app.module.admin.admin_routes import router as admin_routes
from src.app.module.auth.auth_routes import router as auth_routes
from src.app.module.chat.chat_routes import router as chat_routes
from src.app.module.feedback.feedback_routes import router as feedback_routes
from src.app.module.manage.manage_routes import router as manage_routes
from src.app.module.notification.notification_routes import (
    router as notification_routes,
)
from src.app.module.payment.payment_routes import router as payment_routes
from src.app.module.review.review_routes import router as review_routes
from src.app.module.subscription.subscription_routes import (
    router as subscription_routes,
)
from src.app.module.user.user_routes import router as user_routes

router = APIRouter(prefix="/api/v1")

module_routes: list[dict[str, Any]] = [
    {"path": "/auth", "route": auth_routes},
    {"path": "/user", "route": user_routes},
    {"path": "/admin", "route": admin_routes},
    {"path": "/manage", "route": manage_routes},
    {"path": "/notification", "route": notification_routes},
    {"path": "/subscription", "route": subscription_routes},
    {"path": "/payment", "route": payment_routes},
    {"path": "/feedback", "route": feedback_routes},
    {"path": "/review", "route": review_routes},
    {"path": "/chat", "route": chat_routes},
]

for route in module_routes:
    router.include_router(route["route"], prefix=route["path"])
