from typing import Any

from src.app.module.user.user_model import User
from src.connection.socket_server import sio
from src.socket.emit_error import emit_error
from src.socket.emit_result import emit_result
from src.util.enum import EnumSocketEvent
from src.util.http_status import status
from src.util.socket_catch_async import socket_catch_async
from src.util.validate_socket_fields import validate_socket_fields


@socket_catch_async
async def validate_user(sid: str, payload: dict[str, Any]) -> User | None:
    if not payload.get("userId"):
        await emit_error(
            sid, status.BAD_REQUEST, "userId is required to connect", "disconnect"
        )
        return None

    user = await User.get(payload["userId"])

    if not user:
        await emit_error(sid, status.NOT_FOUND, "User not found", "disconnect")
        return None

    return user


@socket_catch_async
async def update_online_status(sid: str, payload: dict[str, Any]) -> None:
    await validate_socket_fields(sid, payload, ["userId", "isOnline"])
    user_id = payload["userId"]
    is_online = payload["isOnline"]

    updated_user = await User.get(user_id)
    if not updated_user:
        await emit_error(sid, status.NOT_FOUND, "User not found")
        return

    updated_user.isOnline = is_online
    await updated_user.save()

    await sio.emit(
        EnumSocketEvent.ONLINE_STATUS,
        emit_result(
            {
                "statusCode": status.OK,
                "success": True,
                "message": f"You are {'online' if updated_user.isOnline else 'offline'}",
                "data": {"isOnline": updated_user.isOnline},
            }
        ),
        to=sid,
    )


@socket_catch_async
async def update_location(sid: str, payload: dict[str, Any]) -> None:
    await validate_socket_fields(sid, payload, ["userId", "lat", "long"])

    user_id = payload["userId"]
    lat = payload["lat"]
    long = payload["long"]

    updated_user = await User.get(user_id)
    if not updated_user:
        await emit_error(sid, status.NOT_FOUND, "User not found")
        return

    updated_user.locationCoordinates = {  # type: ignore[assignment]
        "type": "Point",
        "coordinates": [float(long), float(lat)],
    }
    await updated_user.save()

    # Broadcast to everyone (consider throttling in production)
    await sio.emit(
        EnumSocketEvent.UPDATE_LOCATION,
        emit_result(
            {
                "statusCode": status.OK,
                "success": True,
                "message": "Location updated",
                "data": (
                    updated_user.locationCoordinates.model_dump()
                    if updated_user.locationCoordinates
                    else None
                ),
            }
        ),
    )


class SocketController:
    validate_user = staticmethod(validate_user)
    update_online_status = staticmethod(update_online_status)
    update_location = staticmethod(update_location)
