from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.payment.payment_service import PaymentService
from src.error.api_error import ApiError
from src.util.catch_async import catch_async
from src.util.http_status import status
from src.util.request_body import get_body, get_user
from src.util.send_response import send_response


@catch_async
async def get_public_config(request: Request) -> JSONResponse:
    result = PaymentService.get_public_config()
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Payment configuration retrieved successfully",
            "data": result,
        }
    )


@catch_async
async def create_checkout_session(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    body = await get_body(request)
    result = await PaymentService.create_checkout_session(user, body)
    return send_response(
        {
            "statusCode": 201,
            "success": True,
            "message": "Checkout session created successfully",
            "data": result,
        }
    )


@catch_async
async def create_payment_intent(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    body = await get_body(request)
    result = await PaymentService.create_payment_intent(user, body)
    return send_response(
        {
            "statusCode": 201,
            "success": True,
            "message": "Payment intent created successfully",
            "data": result,
        }
    )


@catch_async
async def handle_webhook(request: Request) -> JSONResponse:
    raw_payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    result = await PaymentService.handle_webhook(raw_payload, sig_header)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Webhook processed successfully",
            "data": result,
        }
    )


@catch_async
async def get_my_payments(request: Request) -> JSONResponse:
    user = get_user(request)
    if not user:
        raise ApiError(status.UNAUTHORIZED, "Unauthorized")

    page = int(request.query_params.get("page", 1))
    limit = int(request.query_params.get("limit", 10))
    result = await PaymentService.get_my_payments(user, page=page, limit=limit)
    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "Payment history retrieved successfully",
            "data": result.get("payments", []),
            "meta": result.get("meta"),
        }
    )


class PaymentController:
    get_public_config = staticmethod(get_public_config)
    create_checkout_session = staticmethod(create_checkout_session)
    create_payment_intent = staticmethod(create_payment_intent)
    handle_webhook = staticmethod(handle_webhook)
    get_my_payments = staticmethod(get_my_payments)
