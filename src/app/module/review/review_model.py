from beanie import PydanticObjectId
from pydantic import Field

from src.util.base_document import TimestampedDocument


class Review(TimestampedDocument):
    user: PydanticObjectId
    rating: int = Field(ge=1, le=5)
    review: str

    class Settings:
        name = "reviews"
