from datetime import UTC, datetime

from beanie import Document, Insert, Replace, Save, before_event
from pydantic import Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampedDocument(Document):
    """Mongoose `{ timestamps: true }` equivalent.

    Insert/replace/save are covered by the hook below; raw update calls set
    `updatedAt` explicitly, as Mongoose does for updateOne/findOneAndUpdate.
    """

    createdAt: datetime = Field(default_factory=utcnow)
    updatedAt: datetime = Field(default_factory=utcnow)

    @before_event(Insert, Replace, Save)
    def _touch(self) -> None:
        self.updatedAt = utcnow()
