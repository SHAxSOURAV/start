import sys
from datetime import datetime

from beanie import init_beanie
from pymongo import AsyncMongoClient

from src.app.module.admin.admin_model import Admin
from src.app.module.auth.auth_model import Auth
from src.app.module.auth.session_model import Session
from src.app.module.chat.chat_model import Chat
from src.app.module.chat.message_model import Message
from src.app.module.feedback.feedback_model import Feedback
from src.app.module.manage.manage_model import (
    FAQ,
    AboutUs,
    ContactUs,
    PrivacyPolicy,
    TermsConditions,
)
from src.app.module.notification.admin_notification_model import AdminNotification
from src.app.module.notification.notification_model import Notification
from src.app.module.review.review_model import Review
from src.app.module.user.user_model import User
from src.config import config

DOCUMENT_MODELS = [
    Auth,
    Session,
    User,
    Admin,
    TermsConditions,
    PrivacyPolicy,
    FAQ,
    AboutUs,
    ContactUs,
    Feedback,
    Review,
    Notification,
    AdminNotification,
    Chat,
    Message,
]

client: AsyncMongoClient | None = None


async def connect_db() -> None:
    global client
    try:
        client = AsyncMongoClient(config.database_url)
        db = (
            client[config.database_name]
            if config.database_name
            else client.get_default_database()
        )
        await init_beanie(database=db, document_models=DOCUMENT_MODELS)
        print(
            f"DB connection successful! [{db.name}] at {datetime.now().strftime('%c')}"
        )
    except Exception as err:
        print("DB Connection Error:", err, file=sys.stderr)
        sys.exit(1)


async def disconnect_db() -> None:
    global client
    if client is not None:
        await client.close()
        client = None


def is_db_up() -> bool:
    return client is not None
