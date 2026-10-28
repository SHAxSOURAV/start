from typing import Any

from pydantic import BaseModel, Field

from src.util.enum import EnumNotificationType


class MarkAsReadValidation(BaseModel):
    notificationId: str | None = None
    notificationIds: list[str] | None = None
    isRead: bool = True


class NotificationQueryValidation(BaseModel):
    notificationId: str | None = None
    type: str | None = None
    isRead: bool | None = None


class CreateNotificationValidation(BaseModel):
    toId: str | None = None
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    type: str = EnumNotificationType.SYSTEM
    data: dict[str, Any] = Field(default_factory=dict)
    link: str | None = None
    image: str | None = None
    sendPush: bool = True
