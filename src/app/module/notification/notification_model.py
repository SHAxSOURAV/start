from datetime import datetime
from typing import Any

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from src.util.base_document import TimestampedDocument
from src.util.enum import EnumNotificationType

# Maximum 30-day retention in database before automatic deletion (30 * 24 * 60 * 60 seconds)
NOTIFICATION_TTL_SECONDS = 30 * 24 * 60 * 60


class Notification(TimestampedDocument):
    """User Notification Document Model.

    Stores in-app notifications with automatic 30-day TTL expiration,
    flexible deep-link payload data, category typing, and high-performance indexing.
    """

    toId: PydanticObjectId
    senderId: PydanticObjectId | None = None
    title: str
    message: str
    type: str = EnumNotificationType.SYSTEM
    data: dict[str, Any] = Field(default_factory=dict)
    link: str | None = None
    image: str | None = None
    isRead: bool = False
    readAt: datetime | None = None

    class Settings:
        name = "notifications"
        indexes = [
            # 1. Automatic 30-day TTL expiry index (zero-maintenance auto deletion)
            pymongo.IndexModel(
                [("createdAt", pymongo.ASCENDING)],
                expireAfterSeconds=NOTIFICATION_TTL_SECONDS,
                name="notification_created_at_ttl_idx",
            ),
            # 2. Hot path: User unread notification feed sorted by newest
            pymongo.IndexModel(
                [
                    ("toId", pymongo.ASCENDING),
                    ("isRead", pymongo.ASCENDING),
                    ("createdAt", pymongo.DESCENDING),
                ],
                name="user_unread_feed_idx",
            ),
            # 3. User all notification feed with keyset/offset pagination
            pymongo.IndexModel(
                [("toId", pymongo.ASCENDING), ("createdAt", pymongo.DESCENDING)],
                name="user_all_feed_idx",
            ),
            # 4. Filter notifications by category/type (e.g. chat, system, payment)
            pymongo.IndexModel(
                [
                    ("toId", pymongo.ASCENDING),
                    ("type", pymongo.ASCENDING),
                    ("createdAt", pymongo.DESCENDING),
                ],
                name="user_type_feed_idx",
            ),
        ]
