import pymongo
from beanie import PydanticObjectId
from pydantic import Field

from src.util.base_document import TimestampedDocument


class Chat(TimestampedDocument):
    """Messages live in their own collection keyed by chatId -- storing them
    as an array here would grow the document unboundedly (16 MB cap)."""

    participants: list[PydanticObjectId] = Field(default_factory=list)

    class Settings:
        name = "chats"
        indexes = [
            pymongo.IndexModel([("participants", pymongo.ASCENDING)]),
        ]
