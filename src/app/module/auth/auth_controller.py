from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.auth.auth_service import AuthService
from src.config import config
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_client_ip, get_user
from src.util.send_response import send_response


def _set_refresh_cookie(response: JSONResponse, refresh_token: str) -> None:
    response.set_cookie(
        "refreshToken",
        refresh_token,
        secure=config.env == "production",
        httponly=True,
        samesite="lax",
    )


@catch_async
async def registration_account(request: Request) -> JSONResponse:
    result = await AuthService.registration_account(await get_body(request))

    is_success = (
        result["message"] == "Account created successfully. Please check your email"
    )

    return send_response(
        {
            "statusCode": 200 if is_success else 400,
            "success": is_success,
            "message": result["message"] or "Something went wrong",
            "data": result,
        }
    )


@catch_async
async def resend_activation_code(request: Request) -> JSONResponse:
    await AuthService.resend_activation_code(await get_body(request))
    return send_response(
        {"statusCode": 200, "success": True, "message": "Resent successfully"}
    )


@catch_async
async def activate_account(request: Request) -> JSONResponse:
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    result = await AuthService.activate_account(
        await get_body(request), ip=ip, user_agent=user_agent
    )

    response = send_response(
        {
            "statusCode": 201,
            "success": True,
            "message": "Activation code verified successfully.",
            "data": result,
        }
    )
    _set_refresh_cookie(response, result["refreshToken"])
    return response


@catch_async
async def login_account(request: Request) -> JSONResponse:
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    result = await AuthService.login_account(
        await get_body(request), ip=ip, user_agent=user_agent
    )

    msg = (
        "Log in successful. Account deletion request has been canceled."
        if result.get("isSoftDeleted")
        else "Log in successful"
    )

    response = send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": msg,
            "data": result,
        }
    )
    _set_refresh_cookie(response, result["refreshToken"])
    return response


@catch_async
async def google_sign_in(request: Request) -> JSONResponse:
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    result = await AuthService.google_sign_in(
        await get_body(request), ip=ip, user_agent=user_agent
    )

    msg = (
        "Log in successful. Account deletion request has been canceled."
        if result.get("isSoftDeleted")
        else "Google sign in successful"
    )

    response = send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": msg,
            "data": result,
        }
    )
    _set_refresh_cookie(response, result["refreshToken"])
    return response


@catch_async
async def apple_sign_in(request: Request) -> JSONResponse:
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    result = await AuthService.apple_sign_in(
        await get_body(request), ip=ip, user_agent=user_agent
    )

    msg = (
        "Log in successful. Account deletion request has been canceled."
        if result.get("isSoftDeleted")
        else "Apple sign in successful"
    )

    response = send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": msg,
            "data": result,
        }
    )
    _set_refresh_cookie(response, result["refreshToken"])
    return response


@catch_async
async def change_password(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    await AuthService.change_password(user, await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Password changed successfully!",
        }
    )


@catch_async
async def forgot_pass(request: Request) -> JSONResponse:
    await AuthService.forgot_pass(await get_body(request))
    return send_response(
        {"statusCode": 200, "success": True, "message": "Check your email!"}
    )


@catch_async
async def forget_pass_otp_verify(request: Request) -> JSONResponse:
    result = await AuthService.forget_pass_otp_verify(await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Code verified successfully",
            "data": result,
        }
    )


@catch_async
async def reset_password(request: Request) -> JSONResponse:
    result = await AuthService.reset_password(await get_body(request))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Password has been reset successfully.",
            "data": result,
        }
    )


@catch_async
async def refresh_token(request: Request) -> JSONResponse:
    body = await get_body(request)
    token = request.cookies.get("refreshToken") or body.get("refreshToken")
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    result = await AuthService.refresh_token(token, ip=ip, user_agent=user_agent)

    response = send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Access token refreshed successfully",
            "data": result,
        }
    )
    if "refreshToken" in result:
        _set_refresh_cookie(response, result["refreshToken"])
    return response


@catch_async
async def list_sessions(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    current_session_id = user.get("sessionId")
    sessions = await AuthService.list_sessions(
        user["authId"], current_session_id=current_session_id
    )
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Active sessions retrieved successfully",
            "data": sessions,
        }
    )


@catch_async
async def logout(request: Request) -> JSONResponse:
    user = get_user(request)
    body = await get_body(request)
    token = request.cookies.get("refreshToken") or body.get("refreshToken")
    session_id = user.get("sessionId") if user else None

    await AuthService.logout_current_session(token, session_id=session_id)
    response = send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Logged out successfully",
        }
    )
    response.delete_cookie("refreshToken")
    return response


@catch_async
async def logout_other_devices(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    current_session_id = user.get("sessionId")
    count = await AuthService.logout_other_sessions(
        user["authId"], current_session_id=current_session_id
    )
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": f"Logged out from {count} other device(s) successfully",
            "data": {"revokedCount": count},
        }
    )


@catch_async
async def revoke_session(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    session_id = request.path_params.get("session_id", "")
    await AuthService.revoke_single_session(user["authId"], session_id)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Device session revoked successfully",
        }
    )


@catch_async
async def get_me(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await AuthService.get_me(user)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "User profile retrieved successfully",
            "data": result,
        }
    )


@catch_async
async def delete_me(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    await AuthService.delete_me(user, await get_body(request))
    response = send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": (
                "Account has been deactivated and scheduled for deletion. "
                "It will be permanently removed after 30 days."
            ),
        }
    )
    response.delete_cookie("refreshToken")
    return response


class AuthController:
    get_me = staticmethod(get_me)
    delete_me = staticmethod(delete_me)
    sign_in = staticmethod(login_account)
    sign_up = staticmethod(registration_account)
    google_sign_in = staticmethod(google_sign_in)
    apple_sign_in = staticmethod(apple_sign_in)
    resend_otp = staticmethod(resend_activation_code)
    verify_otp = staticmethod(forget_pass_otp_verify)

    registration_account = staticmethod(registration_account)
    refresh_token = staticmethod(refresh_token)
    activate_account = staticmethod(activate_account)
    login_account = staticmethod(login_account)
    change_password = staticmethod(change_password)
    forgot_pass = staticmethod(forgot_pass)
    reset_password = staticmethod(reset_password)
    forget_pass_otp_verify = staticmethod(forget_pass_otp_verify)
    resend_activation_code = staticmethod(resend_activation_code)
    list_sessions = staticmethod(list_sessions)
    logout = staticmethod(logout)
    logout_other_devices = staticmethod(logout_other_devices)
    revoke_session = staticmethod(revoke_session)
