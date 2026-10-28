import asyncio
from typing import Any

from bson import ObjectId

from src.app.module.review.review_model import Review
from src.app.module.user.user_model import User
from src.builder.query_builder import QueryBuilder, QueryParams
from src.error.api_error import ApiError
from src.types.auth_types import AuthUserPayload
from src.util.base_document import utcnow
from src.util.enum import EnumUserRole
from src.util.http_status import status
from src.util.validate_fields import validate_fields

# `.populate([{ path: "user", select: "-createdAt -updatedAt -__v" }])`
USER_POPULATE_PROJECTION = {"createdAt": 0, "updatedAt": 0, "__v": 0}


async def _populate_users(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    user_ids = {r["user"] for r in reviews if r.get("user")}
    if not user_ids:
        return reviews

    cursor = User.get_pymongo_collection().find(
        {"_id": {"$in": list(user_ids)}}, USER_POPULATE_PROJECTION
    )
    users = {u["_id"]: u for u in await cursor.to_list(length=None)}

    for review in reviews:
        if review.get("user") in users:
            review["user"] = users[review["user"]]

    return reviews


async def post_review() -> Any:
    pass


async def get_all_reviews(
    user_data: AuthUserPayload, query: QueryParams
) -> dict[str, Any]:
    query_obj: dict[str, Any] = (
        {}
        if user_data["role"] == EnumUserRole.ADMIN
        else {"user": ObjectId(str(user_data["userId"]))}
    )

    review_query = (
        QueryBuilder(Review, query_obj, query)
        .search([])
        .filter()
        .sort()
        .paginate()
        .fields()
    )

    result, meta = await asyncio.gather(
        review_query.execute(), review_query.count_total()
    )

    return {"meta": meta, "result": await _populate_users(result)}


async def get_review(
    user_data: AuthUserPayload, query: dict[str, Any]
) -> dict[str, Any]:
    validate_fields(query, ["reviewId"])

    review = await Review.get_pymongo_collection().find_one(
        {"_id": ObjectId(str(query["reviewId"]))}
    )
    if not review:
        raise ApiError(status.NOT_FOUND, "Review not found")

    return review


async def update_review(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    validate_fields(payload, ["reviewId"])

    update_data: dict[str, Any] = {}
    if payload.get("rating"):
        update_data["rating"] = payload["rating"]
    if payload.get("review"):
        update_data["review"] = payload["review"]

    result = await Review.get_pymongo_collection().find_one_and_update(
        {"_id": ObjectId(str(payload["reviewId"]))},
        {"$set": {**update_data, "updatedAt": utcnow()}},
        return_document=True,
    )

    if not result:
        raise ApiError(status.NOT_FOUND, "Review not found")

    return result


async def delete_review(
    user_data: AuthUserPayload, payload: dict[str, Any]
) -> dict[str, Any]:
    validate_fields(payload, ["reviewId"])

    result = await Review.get_pymongo_collection().delete_one(
        {"_id": ObjectId(str(payload["reviewId"]))}
    )

    if not result.deleted_count:
        raise ApiError(status.NOT_FOUND, "Review not found")

    return {
        "acknowledged": result.acknowledged,
        "deletedCount": result.deleted_count,
    }


class ReviewService:
    post_review = staticmethod(post_review)
    get_all_reviews = staticmethod(get_all_reviews)
    get_review = staticmethod(get_review)
    update_review = staticmethod(update_review)
    delete_review = staticmethod(delete_review)
