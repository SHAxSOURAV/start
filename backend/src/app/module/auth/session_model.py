from datetime import datetime

import pymongo
from beanie import PydanticObjectId

from src.util.base_document import TimestampedDocument


class Session(TimestampedDocument):
    authId: PydanticObjectId
    userId: PydanticObjectId
    refreshTokenHash: str
    previousTokenHash: str | None = None
    rotatedAt: datetime | None = None
    device: str = "Unknown Device"
    ip: str = "unknown"
    userAgent: str = ""
    isValid: bool = True
    expiresAt: datetime
    lastActiveAt: datetime

    class Settings:
        name = "sessions"
        indexes = [
            pymongo.IndexModel([("authId", pymongo.ASCENDING)]),
            pymongo.IndexModel([("refreshTokenHash", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel(
                [("expiresAt", pymongo.ASCENDING)],
                expireAfterSeconds=0,
            ),
            pymongo.IndexModel(
                [("authId", pymongo.ASCENDING), ("isValid", pymongo.ASCENDING)]
            ),
        ]
