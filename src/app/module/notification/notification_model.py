import pymongo
from beanie import PydanticObjectId

from src.util.base_document import TimestampedDocument


class Notification(TimestampedDocument):
    toId: PydanticObjectId
    title: str
    message: str
    isRead: bool = False

    class Settings:
        name = "notifications"
        indexes = [
            # Hot path: unread notification list per user
            pymongo.IndexModel(
                [("toId", pymongo.ASCENDING), ("isRead", pymongo.ASCENDING)]
            ),
        ]
