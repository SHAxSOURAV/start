# file_templates.py

MODEL_TEMPLATE = """
import pymongo
from beanie import Indexed, Link, PydanticObjectId

from src.util.base_document import TimestampedDocument


class __Module__(TimestampedDocument):
    # Superfast indexed fields & relations:
    # user: PydanticObjectId
    # or Beanie Link:
    # user: Link[User]

    class Settings:
        name = "__lower__s"
        indexes = [
            # Index all foreign keys participating in queries & $lookup joins:
            # pymongo.IndexModel([("user", pymongo.ASCENDING)]),
        ]
"""

CONTROLLER_TEMPLATE = """
from fastapi import Request
from fastapi.responses import JSONResponse

from src.app.module.__lower__.__lower___service import __Module__Service
from src.util.catch_async import catch_async
from src.util.request_body import get_body, get_query, get_user
from src.util.send_response import send_response


@catch_async
async def create___lower__(request: Request) -> JSONResponse:
    result = await __Module__Service.create___lower__(
        get_user(request), await get_body(request)
    )

    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "__Module__ created",
            "data": result,
        }
    )


@catch_async
async def get___lower__(request: Request) -> JSONResponse:
    result = await __Module__Service.get___lower__(
        get_user(request), get_query(request)
    )

    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "__Module__ retrieved",
            "data": result,
        }
    )


@catch_async
async def get_all___lower__s(request: Request) -> JSONResponse:
    result = await __Module__Service.get_all___lower__s(
        get_user(request), get_query(request)
    )

    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "__Module__s retrieved",
            "data": result,
        }
    )


@catch_async
async def update___lower__(request: Request) -> JSONResponse:
    result = await __Module__Service.update___lower__(
        get_user(request), await get_body(request)
    )

    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "__Module__ updated",
            "data": result,
        }
    )


@catch_async
async def delete___lower__(request: Request) -> JSONResponse:
    result = await __Module__Service.delete___lower__(
        get_user(request), await get_body(request)
    )

    return send_response(
        {
            "statusCode": 200,
            "success": True,
            "message": "__Module__ deleted",
            "data": result,
        }
    )


class __Module__Controller:
    create___lower__ = staticmethod(create___lower__)
    get___lower__ = staticmethod(get___lower__)
    get_all___lower__s = staticmethod(get_all___lower__s)
    update___lower__ = staticmethod(update___lower__)
    delete___lower__ = staticmethod(delete___lower__)
"""

ROUTES_TEMPLATE = """
from fastapi import APIRouter, Depends

from src.app.middleware.auth import auth
from src.app.module.__lower__.__lower___controller import __Module__Controller
from src.config import config

router = APIRouter()

user_only = [Depends(auth(config.auth_level.user))]

router.add_api_route(
    "/post-__lower__",
    __Module__Controller.create___lower__,
    methods=["POST"],
    dependencies=user_only,
)
router.add_api_route(
    "/get-__lower__",
    __Module__Controller.get___lower__,
    methods=["GET"],
    dependencies=user_only,
)
router.add_api_route(
    "/get-all-__lower__s",
    __Module__Controller.get_all___lower__s,
    methods=["GET"],
    dependencies=user_only,
)
router.add_api_route(
    "/update-__lower__",
    __Module__Controller.update___lower__,
    methods=["PATCH"],
    dependencies=user_only,
)
router.add_api_route(
    "/delete-__lower__",
    __Module__Controller.delete___lower__,
    methods=["DELETE"],
    dependencies=user_only,
)
"""

SERVICE_TEMPLATE = """
import asyncio
from typing import Any

from bson import ObjectId

from src.app.module.__lower__.__lower___model import __Module__
from src.builder.query_builder import QueryBuilder
from src.error.api_error import ApiError
from src.util.http_status import status
from src.util.validate_fields import validate_fields


async def create___lower__(user_data: Any, payload: Any) -> Any:
    # Add your logic here
    pass


async def get___lower__(user_data: Any, query: Any) -> Any:
    validate_fields(query, ["__lower__Id"])

    __lower__ = await __Module__.get_pymongo_collection().find_one(
        {"_id": ObjectId(str(query["__lower__Id"]))}
    )

    if not __lower__:
        raise ApiError(status.NOT_FOUND, "__Module__ not found")

    return __lower__


async def get_all___lower__s(user_data: Any, query: Any) -> Any:
    __lower___query = (
        QueryBuilder(__Module__, {}, query)
        .search([])
        .filter()
        .sort()
        .paginate()
        .fields()
    )

    __lower__s, meta = await asyncio.gather(
        __lower___query.execute(), __lower___query.count_total()
    )

    return {"meta": meta, "__lower__s": __lower__s}


async def update___lower__(user_data: Any, payload: Any) -> Any:
    # Add your logic here
    pass


async def delete___lower__(user_data: Any, payload: Any) -> Any:
    validate_fields(payload, ["__lower__Id"])

    result = await __Module__.get_pymongo_collection().delete_one(
        {"_id": ObjectId(str(payload["__lower__Id"]))}
    )

    if not result.deleted_count:
        raise ApiError(status.NOT_FOUND, "__Module__ not found")

    return {"deletedCount": result.deleted_count}


class __Module__Service:
    create___lower__ = staticmethod(create___lower__)
    get___lower__ = staticmethod(get___lower__)
    get_all___lower__s = staticmethod(get_all___lower__s)
    update___lower__ = staticmethod(update___lower__)
    delete___lower__ = staticmethod(delete___lower__)
"""


def _render(template: str, module_name: str) -> str:
    return template.replace("__Module__", module_name).replace(
        "__lower__", module_name.lower()
    )


def model_template(module_name: str) -> str:
    return _render(MODEL_TEMPLATE, module_name)


def controller_template(module_name: str) -> str:
    return _render(CONTROLLER_TEMPLATE, module_name)


def routes_template(module_name: str) -> str:
    return _render(ROUTES_TEMPLATE, module_name)


def service_template(module_name: str) -> str:
    return _render(SERVICE_TEMPLATE, module_name)
