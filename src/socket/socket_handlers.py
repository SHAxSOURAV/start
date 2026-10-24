from typing import Any

from src.connection.socket_server import sio
from src.socket.chat_socket_controller import ChatSocketController
from src.socket.socket_auth import socket_auth
from src.socket.socket_controller import SocketController
from src.util.enum import EnumSocketEvent, EnumUserRole

GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


def register_socket_handlers() -> None:
    @sio.event
    async def connect(
        sid: str, environ: dict[str, Any], auth: dict[str, Any] | None = None
    ) -> None:
        # Authenticates the handshake; refusing here surfaces as connect_error
        user = await socket_auth(environ, auth)
        await sio.save_session(sid, {"user": user})

        # Set by socket_auth -- never trust client-supplied ids
        user_id = user["userId"]

        validated = await SocketController.validate_user(sid, {"userId": user_id})
        if not validated:
            return

        await sio.enter_room(sid, user_id)
        if user.get("role") in [EnumUserRole.ADMIN, EnumUserRole.SUPER_ADMIN]:
            await sio.enter_room(sid, "admin")

        print(user_id, f"{GREEN}connected{RESET}")

        await SocketController.update_online_status(
            sid, {"userId": user_id, "isOnline": True}
        )

    @sio.on(EnumSocketEvent.UPDATE_LOCATION)
    async def on_update_location(sid: str, payload: dict[str, Any]) -> None:
        session = await sio.get_session(sid)
        user_id = session["user"]["userId"]
        await SocketController.update_location(
            sid, {**(payload or {}), "userId": user_id}
        )

    @sio.on(EnumSocketEvent.SEND_MESSAGE)
    async def on_send_message(sid: str, payload: dict[str, Any]) -> None:
        session = await sio.get_session(sid)
        user_id = session["user"]["userId"]
        await ChatSocketController.send_message(
            sid, {**(payload or {}), "userId": user_id}
        )

    @sio.event
    async def disconnect(sid: str) -> None:
        session = await sio.get_session(sid)
        user_id = session["user"]["userId"]

        await SocketController.update_online_status(
            sid, {"userId": user_id, "isOnline": False}
        )

        print(user_id, f"{RED}disconnected{RESET}")
