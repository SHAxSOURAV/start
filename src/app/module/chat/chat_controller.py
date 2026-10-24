from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.chat.chat_service import ChatService
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_query, get_user
from src.util.send_response import send_response


@catch_async
async def post_chat(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await ChatService.post_chat(user, await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Chat initiated",
            "data": result,
        }
    )


@catch_async
async def get_chat_messages(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await ChatService.get_chat_messages(user, get_query(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Chat retrieved",
            "data": result,
        }
    )


@catch_async
async def get_all_chats(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await ChatService.get_all_chats(user)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Chats retrieved",
            "data": result,
        }
    )


@catch_async
async def update_message_as_seen(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await ChatService.update_message_as_seen(user, await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Message updated as seen",
            "data": result,
        }
    )


class ChatController:
    post_chat = staticmethod(post_chat)
    get_chat_messages = staticmethod(get_chat_messages)
    get_all_chats = staticmethod(get_all_chats)
    update_message_as_seen = staticmethod(update_message_as_seen)
