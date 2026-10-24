from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.module.chat.chat_controller import ChatController
from src.config import config

router = APIRouter()

user_only = [Depends(auth(config.auth_level.user))]

router.add_api_route(
    "/post-chat", ChatController.post_chat, methods=["POST"], dependencies=user_only
)
router.add_api_route(
    "/get-chat-messages",
    ChatController.get_chat_messages,
    methods=["GET"],
    dependencies=user_only,
)
router.add_api_route(
    "/get-all-chats",
    ChatController.get_all_chats,
    methods=["GET"],
    dependencies=user_only,
)
router.add_api_route(
    "/update-message-as-seen",
    ChatController.update_message_as_seen,
    methods=["PATCH"],
    dependencies=user_only,
)
