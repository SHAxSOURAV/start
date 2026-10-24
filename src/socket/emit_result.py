from typing import Any


def emit_result(payload: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "statusCode": payload["statusCode"],
        "success": payload["success"],
        "message": payload["message"],
    }

    data = payload.get("data")
    if data:
        result["data"] = data

    return result
