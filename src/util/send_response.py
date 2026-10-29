from typing import Any

from fastapi.responses import JSONResponse

from src.util.serialize import serialize


def send_response(data: dict[str, Any]) -> JSONResponse:
    response_data: dict[str, Any] = {
        "statusCode": data["statusCode"],
        "success": data["success"],
    }

    if data.get("message") is not None:
        response_data["message"] = data["message"]
    if data.get("activationToken") is not None:
        response_data["activationToken"] = data["activationToken"]
    if data.get("meta") is not None:
        response_data["meta"] = data["meta"]
    if data.get("data") is not None:
        response_data["data"] = data["data"]

    return JSONResponse(
        status_code=data["statusCode"], content=serialize(response_data)
    )
