from datetime import datetime
from typing import Any

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from src.util.base_document import TimestampedDocument
from src.util.enum import EnumSubscriptionStatus, EnumSubscriptionStore


class Subscription(TimestampedDocument):
    """User Subscription State Document.

    Stores in-app purchase and subscription entitlements synced via RevenueCat webhooks.
    Indexed for fast sub-millisecond access-control checks on premium endpoints.
    """

    userId: PydanticObjectId
    appUserId: str
    originalAppUserId: str | None = None
    aliases: list[str] = Field(default_factory=list)

    status: str = EnumSubscriptionStatus.NONE
    productId: str | None = None
    entitlements: list[str] = Field(default_factory=list)
    store: str = EnumSubscriptionStore.UNKNOWN
    environment: str = "SANDBOX"  # "SANDBOX" or "PRODUCTION"

    purchasedAt: datetime | None = None
    expiresAt: datetime | None = None
    unsubscribeDetectedAt: datetime | None = None
    isAutoRenewing: bool = True
    cancelReason: str | None = None

    rawEvent: dict[str, Any] = Field(default_factory=dict)

    class Settings:
        name = "subscriptions"
        indexes = [
            # 1. Unique index per user for 1:1 user-to-subscription mapping
            pymongo.IndexModel(
                [("userId", pymongo.ASCENDING)],
                unique=True,
                name="subscription_user_id_unique_idx",
            ),
            # 2. Fast lookup by RevenueCat app_user_id
            pymongo.IndexModel(
                [("appUserId", pymongo.ASCENDING)],
                name="subscription_app_user_id_idx",
            ),
            # 3. Fast entitlement & status checks
            pymongo.IndexModel(
                [
                    ("status", pymongo.ASCENDING),
                    ("entitlements", pymongo.ASCENDING),
                    ("expiresAt", pymongo.DESCENDING),
                ],
                name="subscription_entitlement_status_idx",
            ),
        ]
