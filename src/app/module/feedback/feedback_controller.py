from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.feedback.feedback_service import FeedbackService
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_query, get_user
from src.util.send_response import send_response


@catch_async
async def post_feedback(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await FeedbackService.post_feedback(user, await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Feedback posted",
            "data": result,
        }
    )


@catch_async
async def get_feedback(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await FeedbackService.get_feedback(user, get_query(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Feedback retrieved",
            "data": result,
        }
    )


@catch_async
async def get_my_feedback(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await FeedbackService.get_my_feedback(user)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Feedback retrieved",
            "data": result,
        }
    )


@catch_async
async def get_all_feedbacks(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await FeedbackService.get_all_feedbacks(user, get_query(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Feedback retrieved",
            "data": result,
        }
    )


@catch_async
async def update_feedback_with_reply(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await FeedbackService.update_feedback_with_reply(
        user, await get_body(request)
    )
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Feedback replied",
            "data": result,
        }
    )


@catch_async
async def delete_feedback(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await FeedbackService.delete_feedback(user, await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Feedback deleted",
            "data": result,
        }
    )


class FeedbackController:
    post_feedback = staticmethod(post_feedback)
    get_feedback = staticmethod(get_feedback)
    get_my_feedback = staticmethod(get_my_feedback)
    get_all_feedbacks = staticmethod(get_all_feedbacks)
    update_feedback_with_reply = staticmethod(update_feedback_with_reply)
    delete_feedback = staticmethod(delete_feedback)
