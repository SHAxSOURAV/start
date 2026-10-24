from datetime import datetime
from typing import Any

import pymongo
from pydantic import Field

from src.util.base_document import TimestampedDocument
from src.util.enum import EnumNotificationType

# Maximum 30-day retention in database before automatic deletion
ADMIN_NOTIFICATION_TTL_SECONDS = 30 * 24 * 60 * 60


class AdminNotification(TimestampedDocument):
    """Admin Broadcast Notification Document Model.

    Stores system-level notifications for platform administrators with automatic 30-day TTL expiration.
    """

    title: str
    message: str
    type: str = EnumNotificationType.SYSTEM
    data: dict[str, Any] = Field(default_factory=dict)
    link: str | None = None
    image: str | None = None
    isRead: bool = False
    readAt: datetime | None = None

    class Settings:
        name = "adminnotifications"
        indexes = [
            # 1. Automatic 30-day TTL expiry index (zero-maintenance auto deletion)
            pymongo.IndexModel(
                [("createdAt", pymongo.ASCENDING)],
                expireAfterSeconds=ADMIN_NOTIFICATION_TTL_SECONDS,
                name="admin_notification_ttl_idx",
            ),
            # 2. Unread admin notifications
            pymongo.IndexModel(
                [("isRead", pymongo.ASCENDING), ("createdAt", pymongo.DESCENDING)],
                name="admin_unread_feed_idx",
            ),
            # 3. All admin notifications pagination
            pymongo.IndexModel(
                [("createdAt", pymongo.DESCENDING)],
                name="admin_all_feed_idx",
            ),
        ]
