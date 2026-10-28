from typing import Any

import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from src.util.base_document import TimestampedDocument
from src.util.enum import EnumPaymentStatus


class Payment(TimestampedDocument):
    userId: PydanticObjectId
    userEmail: str | None = None
    amount: float
    currency: str = "usd"
    status: str = EnumPaymentStatus.PENDING
    stripePaymentIntentId: str | None = None
    stripeSessionId: str | None = None
    stripeCustomerId: str | None = None
    paymentMethod: str | None = "card"
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    receiptUrl: str | None = None
    failureReason: str | None = None

    class Settings:
        name = "payments"
        indexes = [
            pymongo.IndexModel([("userId", pymongo.ASCENDING)]),
            pymongo.IndexModel(
                [("stripePaymentIntentId", pymongo.ASCENDING)],
                sparse=True,
            ),
            pymongo.IndexModel(
                [("stripeSessionId", pymongo.ASCENDING)],
                sparse=True,
            ),
            pymongo.IndexModel([("status", pymongo.ASCENDING)]),
            pymongo.IndexModel([("createdAt", pymongo.DESCENDING)]),
            pymongo.IndexModel(
                [("userId", pymongo.ASCENDING), ("status", pymongo.ASCENDING)]
            ),
        ]
