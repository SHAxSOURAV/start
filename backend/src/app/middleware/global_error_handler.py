import traceback
from typing import Any

import jwt as pyjwt
from bson.errors import InvalidId
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, PyMongoError

from src.app.middleware.limiter import RateLimitError
from src.config import config
from src.error.api_error import ApiError
from src.error.handle_cast_error import handle_cast_error
from src.error.handle_request_validation_error import (
    handle_request_validation_error,
)
from src.error.handle_upload_error import UploadError, handle_upload_error
from src.error.handle_validation_error import handle_validation_error
from src.error.request_schema_error import RequestSchemaError
from src.util.create_error_message import create_error_message
from src.util.delete_uploaded_files import delete_uploaded_files
from src.util.logger import error_logger
from src.util.send_response import send_response


def _respond(
    request: Request, error: Exception, resolved: dict[str, Any]
) -> JSONResponse:
    log_error = print
    log_error("\u274c globalErrorHandler", repr(error))
    error_logger.error(str(error))

    # Roll back anything the request had already written to disk
    delete_uploaded_files(getattr(request.state, "uploaded_files", None))
    request.state.uploaded_files = None

    status_code = resolved["statusCode"]
    if not isinstance(status_code, int) or status_code < 100 or status_code > 599:
        status_code = 500

    response: dict[str, Any] = {
        "success": False,
        "statusCode": status_code,
        "message": resolved["message"],
        "errorMessages": resolved["errorMessages"],
    }

    if config.env != "production":
        response["stack"] = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

    return JSONResponse(status_code=status_code, content=response)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RateLimitError)
    async def _rate_limit(request: Request, error: RateLimitError) -> JSONResponse:
        response = send_response(
            {
                "statusCode": 429,
                "success": False,
                "message": "Too many requests please try again later",
            }
        )
        response.headers["RateLimit-Limit"] = str(error.limit)
        response.headers["RateLimit-Remaining"] = "0"
        response.headers["RateLimit-Reset"] = str(error.reset_seconds)
        return response

    @app.exception_handler(ApiError)
    async def _api_error(request: Request, error: ApiError) -> JSONResponse:
        return _respond(
            request,
            error,
            {
                "statusCode": error.status_code,
                "message": error.message,
                "errorMessages": create_error_message(error.message),
            },
        )

    @app.exception_handler(RequestSchemaError)
    async def _request_schema(
        request: Request, error: RequestSchemaError
    ) -> JSONResponse:
        return _respond(request, error, handle_request_validation_error(error.error))

    @app.exception_handler(ValidationError)
    async def _document_validation(
        request: Request, error: ValidationError
    ) -> JSONResponse:
        return _respond(request, error, handle_validation_error(error))

    @app.exception_handler(UploadError)
    async def _upload(request: Request, error: UploadError) -> JSONResponse:
        return _respond(request, error, handle_upload_error(error))

    @app.exception_handler(pyjwt.ExpiredSignatureError)
    async def _expired(
        request: Request, error: pyjwt.ExpiredSignatureError
    ) -> JSONResponse:
        return _respond(
            request,
            error,
            {
                "statusCode": 401,
                "message": "Token has expired",
                "errorMessages": create_error_message(str(error) or "Token expired"),
            },
        )

    @app.exception_handler(pyjwt.PyJWTError)
    async def _jwt(request: Request, error: pyjwt.PyJWTError) -> JSONResponse:
        return _respond(
            request,
            error,
            {
                "statusCode": 401,
                "message": "Invalid token",
                "errorMessages": create_error_message(str(error) or "Invalid token"),
            },
        )

    @app.exception_handler(InvalidId)
    async def _cast(request: Request, error: InvalidId) -> JSONResponse:
        return _respond(request, error, handle_cast_error())

    @app.exception_handler(DuplicateKeyError)
    async def _duplicate(request: Request, error: DuplicateKeyError) -> JSONResponse:
        key_value = (error.details or {}).get("keyValue") or {}
        field = next(iter(key_value), None)
        if field is None:
            key_pattern = (error.details or {}).get("keyPattern") or {}
            field = next(iter(key_pattern), "field")
        message = f"{field} must be unique"
        return _respond(
            request,
            error,
            {
                "statusCode": 409,
                "message": message,
                "errorMessages": create_error_message(message, field),
            },
        )

    @app.exception_handler(TypeError)
    async def _type_error(request: Request, error: TypeError) -> JSONResponse:
        message = str(error) or "Type Error"
        return _respond(
            request,
            error,
            {
                "statusCode": 400,
                "message": message,
                "errorMessages": create_error_message(message),
            },
        )

    @app.exception_handler(PyMongoError)
    async def _mongo(request: Request, error: PyMongoError) -> JSONResponse:
        message = str(error) or "Mongo Error"
        return _respond(
            request,
            error,
            {
                "statusCode": 500,
                "message": message,
                "errorMessages": create_error_message(message),
            },
        )

    @app.exception_handler(Exception)
    async def _fallback(request: Request, error: Exception) -> JSONResponse:
        message = str(error) or "Something went wrong!"
        return _respond(
            request,
            error,
            {
                "statusCode": 500,
                "message": message,
                "errorMessages": create_error_message(message),
            },
        )
