from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.subscription.subscription_service import SubscriptionService
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_query, get_user
from src.util.send_response import send_response


@catch_async
async def revenuecat_webhook(request: Request) -> JSONResponse:
    """Public webhook receiver for RevenueCat subscription events."""
    auth_header = request.headers.get("authorization")
    payload = await get_body(request)

    result = await SubscriptionService.handle_webhook(payload, auth_header)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "RevenueCat webhook processed",
            "data": result,
        }
    )


@catch_async
async def get_my_subscription(request: Request) -> JSONResponse:
    """Authenticated user retrieves their active subscription details."""
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    result = await SubscriptionService.get_my_subscription(str(user["userId"]))
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Subscription details retrieved",
            "data": result,
        }
    )


@catch_async
async def check_entitlement(request: Request) -> JSONResponse:
    """Checks whether the authenticated user has an active entitlement."""
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    query = get_query(request)
    entitlement = query.get("entitlement", "pro")

    result = await SubscriptionService.check_user_entitlement(
        str(user["userId"]), str(entitlement)
    )
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Entitlement status checked",
            "data": result,
        }
    )


class SubscriptionController:
    revenuecat_webhook = staticmethod(revenuecat_webhook)
    get_my_subscription = staticmethod(get_my_subscription)
    check_entitlement = staticmethod(check_entitlement)
