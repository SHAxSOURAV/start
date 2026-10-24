"""Mongoose CastError equivalent: an id that is not a valid ObjectId."""

from typing import Any


def handle_cast_error(path: str = "") -> dict[str, Any]:
    error_message = {"path": path, "message": "Invalid Id"}

    return {
        "statusCode": 400,
        "message": "CastError -> Please Provide Valid ObjectID",
        "errorMessages": [error_message],
    }
