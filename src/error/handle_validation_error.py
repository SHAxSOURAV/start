"""Document validation errors raised by the Beanie/Pydantic model layer."""

from typing import Any

from pydantic import ValidationError


def handle_validation_error(err: ValidationError) -> dict[str, Any]:
    errors: list[dict[str, Any]] = [
        {
            "path": ".".join(str(p) for p in issue["loc"]),
            "message": issue.get("msg") or "Validation failed",
        }
        for issue in err.errors()
    ]

    joined = ", ".join(e["message"] for e in errors)

    return {
        "statusCode": 400,
        "message": f"Validation Error: {joined}",
        "errorMessages": errors,
    }
