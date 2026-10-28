import pymongo
from beanie import PydanticObjectId

from src.util.base_document import TimestampedDocument


class Message(TimestampedDocument):
    chatId: PydanticObjectId
    sender: PydanticObjectId
    receiver: PydanticObjectId
    message: str
    isRead: bool = False

    class Settings:
        name = "messages"
        indexes = [
            # Hot path: paginated message history for a chat, newest first
            pymongo.IndexModel(
                [("chatId", pymongo.ASCENDING), ("createdAt", pymongo.DESCENDING)]
            ),
            # Hot path: unread counts per receiver
            pymongo.IndexModel(
                [("receiver", pymongo.ASCENDING), ("isRead", pymongo.ASCENDING)]
            ),
        ]
