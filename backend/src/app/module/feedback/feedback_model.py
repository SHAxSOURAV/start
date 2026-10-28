from beanie import PydanticObjectId

from src.util.base_document import TimestampedDocument


class Feedback(TimestampedDocument):
    user: PydanticObjectId | None = None
    name: str
    email: str
    feedback: str
    reply: str | None = None

    class Settings:
        name = "feedbacks"
