from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.module.notification.notification_controller import (
    NotificationController,
)
from src.config import config

router = APIRouter()

user_only = [Depends(auth(config.auth_level.user))]

# 1. Feed & Single Details
router.add_api_route(
    "/get-all-notifications",
    NotificationController.get_all_notifications,
    methods=["GET"],
    dependencies=user_only,
)
router.add_api_route(
    "/get-notification",
    NotificationController.get_notification,
    methods=["GET"],
    dependencies=user_only,
)
router.add_api_route(
    "/unread-count",
    NotificationController.get_unread_count,
    methods=["GET"],
    dependencies=user_only,
)

# 2. Read / Unread Status Actions
router.add_api_route(
    "/mark-as-read",
    NotificationController.mark_as_read,
    methods=["PATCH"],
    dependencies=user_only,
)
router.add_api_route(
    "/mark-all-as-read",
    NotificationController.mark_all_as_read,
    methods=["PATCH"],
    dependencies=user_only,
)
router.add_api_route(
    "/update-as-mark-unread",
    NotificationController.update_as_read_unread,
    methods=["PATCH"],
    dependencies=user_only,
)

# 3. Deletion Actions
router.add_api_route(
    "/delete-notification",
    NotificationController.delete_notification,
    methods=["DELETE"],
    dependencies=user_only,
)
router.add_api_route(
    "/clear-all",
    NotificationController.clear_all_notifications,
    methods=["DELETE"],
    dependencies=user_only,
)
