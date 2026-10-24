from datetime import datetime

import pymongo
from beanie import PydanticObjectId

from src.util.base_document import TimestampedDocument


class Admin(TimestampedDocument):
    authId: PydanticObjectId
    name: str
    email: str
    profile_image: str | None = None
    phoneNumber: str | None = None
    address: str | None = None
    isDeleted: bool | None = False
    deletedAt: datetime | None = None

    class Settings:
        name = "admins"
        indexes = [
            pymongo.IndexModel([("authId", pymongo.ASCENDING)]),
            pymongo.IndexModel([("email", pymongo.ASCENDING)]),
            pymongo.IndexModel(
                [("isDeleted", pymongo.ASCENDING), ("deletedAt", pymongo.ASCENDING)]
            ),
        ]
