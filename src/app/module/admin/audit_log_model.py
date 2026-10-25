from __future__ import annotations

from typing import Any

import pymongo
from beanie import PydanticObjectId

from src.util.base_document import TimestampedDocument


class AuditLog(TimestampedDocument):
    action: str  # e.g. "USER_BAN", "USER_UNBAN", "USER_SUSPEND", "USER_UNAPPROVE", "USER_ACTIVATE"
    performedBy: PydanticObjectId  # Admin Auth ID
    performedByRole: str  # Role of admin who performed the action
    targetAuthId: PydanticObjectId  # Target Auth ID
    targetUserId: PydanticObjectId | None = None  # Target User profile ID
    targetEmail: str
    targetRole: str
    reason: str | None = None  # User-facing reason
    internalNote: str | None = None  # Internal admin note
    oldStatus: str
    newStatus: str
    ip: str | None = None
    userAgent: str | None = None
    metadata: dict[str, Any] | None = None

    class Settings:
        name = "audit_logs"
        indexes = [
            pymongo.IndexModel([("performedBy", pymongo.ASCENDING)]),
            pymongo.IndexModel([("targetAuthId", pymongo.ASCENDING)]),
            pymongo.IndexModel([("action", pymongo.ASCENDING)]),
            pymongo.IndexModel([("createdAt", pymongo.DESCENDING)]),
        ]
