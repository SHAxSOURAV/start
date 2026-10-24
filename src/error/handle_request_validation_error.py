"""Request-schema validation errors (the zod error translator's counterpart)."""

from typing import Any

from pydantic import ValidationError

_VALUE_ERROR_PREFIX = "Value error, "


def handle_request_validation_error(error: ValidationError) -> dict[str, Any]:
    error_messages = []
    for issue in error.errors():
        loc = [str(p) for p in issue["loc"]]
        # Drop the leading "body"/"query"/"params" segment for readable paths
        path = ".".join(loc[1:]) or (loc[0] if loc else "")

        message = issue["msg"]
        # Pydantic prefixes messages raised inside validators; the schemas
        # carry the exact wording the client should see
        if message.startswith(_VALUE_ERROR_PREFIX):
            message = message[len(_VALUE_ERROR_PREFIX) :]

        error_messages.append({"path": path, "message": message})

    return {
        "statusCode": 400,
        "message": "Validation error",
        "errorMessages": error_messages,
    }
