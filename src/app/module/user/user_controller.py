from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.user.user_service import UserService
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_user
from src.util.send_response import send_response


@catch_async
async def update_profile(request: Request) -> JSONResponse:
    result = await UserService.update_profile(request)

    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Profile updated successfully",
            "data": result,
        }
    )


@catch_async
async def get_profile(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await UserService.get_profile(user)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "User retrieved successfully",
            "data": result,
        }
    )


@catch_async
async def delete_my_account(request: Request) -> JSONResponse:
    await UserService.delete_my_account(await get_body(request))
    return send_response(
        {"statusCode": 200, "success": True, "message": "Account deleted!"}
    )


class UserController:
    delete_my_account = staticmethod(delete_my_account)
    get_profile = staticmethod(get_profile)
    update_profile = staticmethod(update_profile)
