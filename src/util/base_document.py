from datetime import UTC, datetime

from beanie import Document, Insert, Replace, Save, before_event
from pydantic import Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class TimestampedDocument(Document):
    """Mongoose `{ timestamps: true }` equivalent with built-in Soft Delete.

    Insert/replace/save are covered by the hook below; raw update calls set
    `updatedAt` explicitly, as Mongoose does for updateOne/findOneAndUpdate.
    """

    createdAt: datetime = Field(default_factory=utcnow)
    updatedAt: datetime = Field(default_factory=utcnow)
    isDeleted: bool | None = False
    deletedAt: datetime | None = None

    @before_event(Insert, Replace, Save)
    def _touch(self) -> None:
        self.updatedAt = utcnow()

    async def soft_delete(self) -> None:
        """Marks the document as soft-deleted without physically removing it from the database."""
        now = utcnow()
        self.isDeleted = True
        self.deletedAt = now
        self.updatedAt = now
        await self.save()

    async def restore(self) -> None:
        """Restores a soft-deleted document."""
        self.isDeleted = False
        self.deletedAt = None
        self.updatedAt = utcnow()
        await self.save()


BaseDocument = TimestampedDocument
