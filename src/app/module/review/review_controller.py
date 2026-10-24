from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.review.review_service import ReviewService
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_query, get_user
from src.util.send_response import send_response


@catch_async
async def post_review(request: Request) -> JSONResponse:
    result = await ReviewService.post_review()
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Review posted",
            "data": result,
        }
    )


@catch_async
async def get_all_reviews(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await ReviewService.get_all_reviews(user, get_query(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Review retrieved",
            "data": result,
        }
    )


@catch_async
async def get_review(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await ReviewService.get_review(user, get_query(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Review retrieved",
            "data": result,
        }
    )


@catch_async
async def update_review(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await ReviewService.update_review(user, await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Review updated",
            "data": result,
        }
    )


@catch_async
async def delete_review(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await ReviewService.delete_review(user, get_query(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Review deleted",
            "data": result,
        }
    )


class ReviewController:
    post_review = staticmethod(post_review)
    get_all_reviews = staticmethod(get_all_reviews)
    get_review = staticmethod(get_review)
    update_review = staticmethod(update_review)
    delete_review = staticmethod(delete_review)
