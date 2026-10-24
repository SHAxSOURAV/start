from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from pydantic import BaseModel, ValidationError

from src.error.request_schema_error import RequestSchemaError
from src.util.request_body import get_body, get_query

# Validates body/query/params against a schema before the controller runs.
# Parsed (and coerced) values are written back to request.state.body so
# services always receive clean data. Failures are formatted by the global
# error handler via handle_request_validation_error.


def validate_request(
    schema: type[BaseModel],
) -> Callable[[Request], Awaitable[None]]:
    async def dependency(request: Request) -> None:
        payload: dict[str, Any] = {
            "body": await get_body(request),
            "query": get_query(request),
            "params": dict(request.path_params),
        }

        try:
            parsed = schema.model_validate(payload)
        except ValidationError as error:
            raise RequestSchemaError(error) from error

        body = getattr(parsed, "body", None)
        if body is not None:
            request.state.body = (
                body.model_dump() if isinstance(body, BaseModel) else body
            )

    return dependency
