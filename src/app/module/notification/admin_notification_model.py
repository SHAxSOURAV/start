from src.util.base_document import TimestampedDocument


class AdminNotification(TimestampedDocument):
    title: str
    message: str
    isRead: bool = False

    class Settings:
        name = "adminnotifications"
