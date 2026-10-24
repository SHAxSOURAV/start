import asyncio
import math
from typing import Any

from bson import ObjectId

from src.app.module.chat.chat_model import Chat
from src.app.module.chat.message_model import Message
from src.app.module.user.user_model import User
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.base_document import utcnow
from src.util.fire_and_forget import fire_and_forget
from src.util.http_status import status
from src.util.post_notification import post_notification
from src.util.serialize import serialize
from src.util.validate_fields import validate_fields

PARTICIPANT_PROJECTION = {"name": 1, "phoneNumber": 1, "profile_image": 1}


async def post_chat(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    user_id = str(user_data["userId"])
    receiver_id = str(payload.get("receiverId"))

    validate_fields(payload, ["receiverId"])

    user, receiver, existing_chat = await asyncio.gather(
        User.get_pymongo_collection().find_one({"_id": ObjectId(user_id)}),
        User.get_pymongo_collection().find_one({"_id": ObjectId(receiver_id)}),
        Chat.get_pymongo_collection().find_one(
            {"participants": {"$all": [ObjectId(user_id), ObjectId(receiver_id)]}}
        ),
    )

    if not user:
        raise ApiError(status.NOT_FOUND, "User not found")
    if not receiver:
        raise ApiError(status.NOT_FOUND, "Receiver not found")
    if existing_chat:
        return existing_chat

    new_chat = Chat(participants=[ObjectId(user_id), ObjectId(receiver_id)])
    await new_chat.insert()

    fire_and_forget(
        post_notification(
            "New message", "You have started a new conversation", receiver_id
        )
    )
    fire_and_forget(
        post_notification("New message", "You have started a new conversation", user_id)
    )

    return serialize(new_chat.model_dump(by_alias=True))


async def get_chat_messages(
    user_data: AuthUserPayload, query: dict[str, Any]
) -> dict[str, Any]:
    """Paginates ONLY the messages while keeping the existing response format.

    Accepts optional `page` & `limit` query params (default 1 & 10).
    """
    validate_fields(query, ["chatId"])

    page = _positive(query.get("page"), 1)
    limit = _positive(query.get("limit"), 10)
    skip = (page - 1) * limit

    chat = await Chat.get_pymongo_collection().find_one(
        {"_id": ObjectId(str(query["chatId"]))}
    )

    if not chat:
        raise ApiError(status.NOT_FOUND, "Chat not found")

    participants = (
        await User.get_pymongo_collection()
        .find({"_id": {"$in": chat.get("participants", [])}}, PARTICIPANT_PROJECTION)
        .to_list(length=None)
    )
    chat["participants"] = participants

    total, messages = await asyncio.gather(
        Message.get_pymongo_collection().count_documents({"chatId": chat["_id"]}),
        Message.get_pymongo_collection()
        .find({"chatId": chat["_id"]})
        .sort([("createdAt", -1)])  # newest first; adjust as needed
        .skip(skip)
        .limit(limit)
        .to_list(length=limit),
    )

    return {
        "meta": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPage": math.ceil(total / limit) or 1,
        },
        **chat,
        "messages": messages,
    }


async def get_all_chats(user_data: AuthUserPayload) -> dict[str, Any]:
    user_id = ObjectId(str(user_data["userId"]))

    pipeline: list[dict[str, Any]] = [
        {"$match": {"participants": {"$in": [user_id]}}},
        {
            "$lookup": {
                "from": "messages",
                "let": {"chatId": "$_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$chatId", "$$chatId"]},
                                    {"$eq": ["$receiver", user_id]},
                                    {"$eq": ["$isRead", False]},
                                ]
                            }
                        }
                    }
                ],
                "as": "unreadMessages",
            }
        },
        {"$addFields": {"unRead": {"$size": "$unreadMessages"}}},
        {
            "$lookup": {
                "from": "users",
                "localField": "participants",
                "foreignField": "_id",
                "as": "participants",
            }
        },
        {"$project": {"unreadMessages": 0}},
    ]

    cursor = await Chat.get_pymongo_collection().aggregate(pipeline)
    chats = await cursor.to_list(length=None)

    return {"chats": chats}


async def update_message_as_seen(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    """Marks every unread message in a chat as seen for the logged-in user,
    i.e. the messages where the logged-in user is the receiver."""
    user_id = user_data["userId"]

    validate_fields(payload, ["chatId"])

    chat = await Chat.get_pymongo_collection().find_one(
        {"_id": ObjectId(str(payload["chatId"]))}
    )

    if not chat:
        raise ApiError(status.NOT_FOUND, "Chat not found")

    result = await Message.get_pymongo_collection().update_many(
        {
            "chatId": chat["_id"],
            "receiver": ObjectId(str(user_id)),
            "isRead": False,
        },
        {"$set": {"isRead": True, "updatedAt": utcnow()}},
    )

    return {
        "acknowledged": result.acknowledged,
        "matchedCount": result.matched_count,
        "modifiedCount": result.modified_count,
    }


def _positive(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if parsed > 0 else fallback


class ChatService:
    post_chat = staticmethod(post_chat)
    get_chat_messages = staticmethod(get_chat_messages)
    get_all_chats = staticmethod(get_all_chats)
    update_message_as_seen = staticmethod(update_message_as_seen)
