from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.manage.manage_service import ManageService
from src.util.catch_async import catch_async
from src.util.request_body import get_body, get_query
from src.util.send_response import send_response


def resolve_upsert_result(result: Any) -> tuple[str, Any]:
    if isinstance(result, dict) and "message" in result:
        return result["message"] or "Successful", result.get("result", result)
    return "Successful", result


def _make_add(service_method: Any) -> Any:
    @catch_async
    async def handler(request: Request) -> JSONResponse:
        result = await service_method(await get_body(request))
        message, data = resolve_upsert_result(result)
        return send_response(
            {"statusCode": 200, "success": True, "message": message, "data": data}
        )

    return handler


def _make_get(service_method: Any) -> Any:
    @catch_async
    async def handler(request: Request) -> JSONResponse:
        data = await service_method()
        return send_response(
            {
                "statusCode": 200,
                "success": True,
                "message": "Successful",
                "data": data,
            }
        )

    return handler


def _make_delete(service_method: Any) -> Any:
    @catch_async
    async def handler(request: Request) -> JSONResponse:
        data = await service_method(get_query(request))
        return send_response(
            {
                "statusCode": 200,
                "success": True,
                "message": "Deletion Successful",
                "data": data,
            }
        )

    return handler


class ManageController:
    add_terms_conditions = _make_add(ManageService.add_terms_conditions)
    get_terms_conditions = _make_get(ManageService.get_terms_conditions)
    delete_terms_conditions = _make_delete(ManageService.delete_terms_conditions)

    add_privacy_policy = _make_add(ManageService.add_privacy_policy)
    get_privacy_policy = _make_get(ManageService.get_privacy_policy)
    delete_privacy_policy = _make_delete(ManageService.delete_privacy_policy)

    add_about_us = _make_add(ManageService.add_about_us)
    get_about_us = _make_get(ManageService.get_about_us)
    delete_about_us = _make_delete(ManageService.delete_about_us)

    add_faq = _make_add(ManageService.add_faq)
    get_faq = _make_get(ManageService.get_faq)
    delete_faq = _make_delete(ManageService.delete_faq)

    add_contact_us = _make_add(ManageService.add_contact_us)
    get_contact_us = _make_get(ManageService.get_contact_us)
    delete_contact_us = _make_delete(ManageService.delete_contact_us)
