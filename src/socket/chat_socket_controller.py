from typing import Any

from src.app.module.chat.chat_model import Chat
from src.app.module.chat.message_model import Message
from src.connection.socket_server import sio
from src.socket.emit_error import emit_error
from src.socket.emit_result import emit_result
from src.util.enum import EnumSocketEvent
from src.util.http_status import status
from src.util.post_notification import post_notification
from src.util.serialize import serialize
from src.util.socket_catch_async import socket_catch_async
from src.util.validate_socket_fields import validate_socket_fields


@socket_catch_async
async def send_message(sid: str, payload: dict[str, Any]) -> Message | None:
    await validate_socket_fields(sid, payload, ["receiverId", "chatId", "message"])
    user_id = payload["userId"]
    receiver_id = payload["receiverId"]
    chat_id = payload["chatId"]
    message = payload["message"]

    existing_chat = await Chat.find_one(
        {
            "_id": _object_id(chat_id),
            "participants": {"$all": [_object_id(user_id), _object_id(receiver_id)]},
        }
    )

    if not existing_chat:
        await emit_error(
            sid,
            status.NOT_FOUND,
            "Chat not found. Make sure chatId, senderId, receiverId are valid",
        )
        return None

    new_message = Message(
        chatId=chat_id, sender=user_id, receiver=receiver_id, message=message
    )
    await new_message.insert()

    # notify both participants upon new message
    await post_notification("New message", message, receiver_id)
    await post_notification("New message", message, user_id)

    envelope = emit_result(
        {
            "statusCode": status.OK,
            "success": True,
            "message": "Message sent successfully",
            "data": serialize(new_message.model_dump(by_alias=True)),
        }
    )

    # Broadcast to user
    await sio.emit(EnumSocketEvent.SEND_MESSAGE, envelope, room=user_id)

    # Broadcast to receiver
    await sio.emit(EnumSocketEvent.SEND_MESSAGE, envelope, room=receiver_id)

    return new_message


def _object_id(value: Any) -> Any:
    from bson import ObjectId

    try:
        return ObjectId(str(value))
    except Exception:
        return value


class ChatSocketController:
    send_message = staticmethod(send_message)
