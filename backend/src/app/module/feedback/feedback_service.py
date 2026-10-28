import asyncio
from typing import Any

from bson import ObjectId

from src.app.module.feedback.feedback_model import Feedback
from src.app.module.user.user_model import User
from src.builder.query_builder import QueryBuilder, QueryParams
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.base_document import utcnow
from src.util.enum import EnumUserRole
from src.util.fire_and_forget import fire_and_forget
from src.util.http_status import status
from src.util.post_notification import post_notification
from src.util.serialize import serialize
from src.util.validate_fields import validate_fields


async def post_feedback(
    user_data: AuthUserPayload | None, payload: dict[str, Any]
) -> dict[str, Any]:
    validate_fields(payload, ["feedback"])

    user: dict[str, Any] | None = None

    if not user_data:
        validate_fields(payload, ["name", "email"])
    else:
        user = await User.get_pymongo_collection().find_one(
            {"_id": ObjectId(str(user_data["userId"]))}
        )

    feedback_data: dict[str, Any] = {"feedback": payload["feedback"]}
    if user_data and user:
        feedback_data["user"] = ObjectId(str(user_data["userId"]))
        feedback_data["name"] = user["name"]
        feedback_data["email"] = user["email"]
    if not user_data:
        feedback_data["name"] = payload.get("name")
        feedback_data["email"] = payload.get("email")

    feedback = Feedback(**feedback_data)
    await feedback.insert()

    if user_data:
        fire_and_forget(
            post_notification(
                "Thank You",
                "Thank you for your valuable feedback 🫡",
                user_data["userId"],
            )
        )

    fire_and_forget(
        post_notification(
            "New Feedback", "Mount Fuji got a new feedback. Check it out!"
        )
    )

    return serialize(feedback.model_dump(by_alias=True))


async def get_feedback(
    user_data: AuthUserPayload, query: dict[str, Any]
) -> dict[str, Any]:
    validate_fields(query, ["feedbackId"])

    feedback = await Feedback.get_pymongo_collection().find_one(
        {"_id": ObjectId(str(query["feedbackId"]))}
    )
    if not feedback:
        raise ApiError(status.NOT_FOUND, "Feedback not found")

    return feedback


async def get_my_feedback(user_data: AuthUserPayload) -> dict[str, Any]:
    user_id = user_data["userId"]

    cursor = Feedback.get_pymongo_collection().find({"user": ObjectId(str(user_id))})
    feedback = await cursor.to_list(length=None)
    if not feedback:
        raise ApiError(status.NOT_FOUND, "Feedback not found")

    return {"count": len(feedback), "feedback": feedback}


async def get_all_feedbacks(
    user_data: AuthUserPayload, query: QueryParams
) -> dict[str, Any]:
    query_obj: dict[str, Any] = (
        {}
        if user_data["role"] == EnumUserRole.ADMIN
        else {"user": ObjectId(str(user_data["userId"]))}
    )

    feedback_query = (
        QueryBuilder(Feedback, query_obj, query)
        .search([])
        .filter()
        .sort()
        .paginate()
        .fields()
    )

    feedback, meta = await asyncio.gather(
        feedback_query.execute(), feedback_query.count_total()
    )

    return {"meta": meta, "feedback": feedback}


async def update_feedback_with_reply(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    validate_fields(payload, ["feedbackId", "reply"])

    feedback = await Feedback.get_pymongo_collection().find_one_and_update(
        {"_id": ObjectId(str(payload["feedbackId"]))},
        {"$set": {"reply": payload["reply"], "updatedAt": utcnow()}},
        return_document=True,
    )

    if not feedback:
        raise ApiError(status.NOT_FOUND, "Feedback not found")

    if feedback.get("user"):
        fire_and_forget(
            post_notification(
                "Feedback Reply",
                "Admin has replied to your feedback",
                str(feedback["user"]),
            )
        )

    return feedback


async def delete_feedback(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    validate_fields(payload, ["feedbackId"])

    result = await Feedback.get_pymongo_collection().delete_one(
        {"_id": ObjectId(str(payload["feedbackId"]))}
    )

    if not result.deleted_count:
        raise ApiError(status.NOT_FOUND, "Feedback not found")

    return {
        "acknowledged": result.acknowledged,
        "deletedCount": result.deleted_count,
    }


class FeedbackService:
    post_feedback = staticmethod(post_feedback)
    get_feedback = staticmethod(get_feedback)
    get_my_feedback = staticmethod(get_my_feedback)
    get_all_feedbacks = staticmethod(get_all_feedbacks)
    update_feedback_with_reply = staticmethod(update_feedback_with_reply)
    delete_feedback = staticmethod(delete_feedback)
