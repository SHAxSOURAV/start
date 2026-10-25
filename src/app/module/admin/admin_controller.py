from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.admin.admin_service import AdminService
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_client_ip, get_user
from src.util.send_response import send_response


@catch_async
async def update_profile(request: Request) -> JSONResponse:
    result = await AdminService.update_profile(request)
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

    result = await AdminService.get_profile(user)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Admin retrieved successfully",
            "data": result,
        }
    )


@catch_async
async def delete_my_account(request: Request) -> JSONResponse:
    await AdminService.delete_my_account(await get_body(request))
    return send_response(
        {"statusCode": 200, "success": True, "message": "Account deleted!"}
    )


@catch_async
async def create_admin(request: Request) -> JSONResponse:
    result = await AdminService.create_admin(await get_body(request))
    return send_response(
        {
            "statusCode": 201,
            "success": True,
            "message": "Admin created successfully",
            "data": result,
        }
    )


@catch_async
async def get_overview_statistics(request: Request) -> JSONResponse:
    refresh = request.query_params.get("refresh", "false").lower() == "true"
    result = await AdminService.get_overview_statistics(refresh=refresh)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Admin overview statistics retrieved successfully",
            "data": result,
        }
    )


@catch_async
async def get_charts_statistics(request: Request) -> JSONResponse:
    refresh = request.query_params.get("refresh", "false").lower() == "true"
    year_param = request.query_params.get("year")
    year = int(year_param) if year_param and year_param.isdigit() else None
    result = await AdminService.get_charts_statistics(year=year, refresh=refresh)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Admin growth charts statistics retrieved successfully",
            "data": result,
        }
    )


@catch_async
async def get_breakdowns_statistics(request: Request) -> JSONResponse:
    refresh = request.query_params.get("refresh", "false").lower() == "true"
    result = await AdminService.get_breakdowns_statistics(refresh=refresh)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Admin breakdown statistics retrieved successfully",
            "data": result,
        }
    )


@catch_async
async def manage_user_status(request: Request) -> JSONResponse:
    target_id = request.path_params.get("id", "")
    admin_user = get_user(request)
    assert admin_user is not None
    body = await get_body(request)
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")

    result = await AdminService.manage_user_status(
        admin_user=admin_user,
        target_id=target_id,
        payload=body,
        ip=ip,
        user_agent=user_agent,
    )

    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": result.get("message", "User status updated successfully"),
            "data": result,
        }
    )


@catch_async
async def get_audit_logs(request: Request) -> JSONResponse:
    query_params = dict(request.query_params)
    result = await AdminService.get_audit_logs(query_params)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Audit logs retrieved successfully",
            "data": result["data"],
            "meta": result["meta"],
        }
    )


@catch_async
async def get_all_users(request: Request) -> JSONResponse:
    query_params = dict(request.query_params)
    result = await AdminService.get_all_users(query_params)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "User list retrieved successfully",
            "data": result["data"],
            "meta": result["meta"],
        }
    )


@catch_async
async def get_banned_users(request: Request) -> JSONResponse:
    query_params = dict(request.query_params)
    query_params["status"] = "BANNED"
    result = await AdminService.get_all_users(query_params)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Banned users retrieved successfully",
            "data": result["data"],
            "meta": result["meta"],
        }
    )


class AdminController:
    create_admin = staticmethod(create_admin)
    update_profile = staticmethod(update_profile)
    get_profile = staticmethod(get_profile)
    delete_my_account = staticmethod(delete_my_account)
    get_overview_statistics = staticmethod(get_overview_statistics)
    get_charts_statistics = staticmethod(get_charts_statistics)
    get_breakdowns_statistics = staticmethod(get_breakdowns_statistics)
    manage_user_status = staticmethod(manage_user_status)
    get_audit_logs = staticmethod(get_audit_logs)
    get_all_users = staticmethod(get_all_users)
    get_banned_users = staticmethod(get_banned_users)


