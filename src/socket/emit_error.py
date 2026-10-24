from src.connection.socket_server import sio
from src.util.enum import EnumSocketEvent
from src.util.http_status import status

RED = "\033[31m"
RESET = "\033[0m"


async def emit_error(
    sid: str,
    status_code: int = status.INTERNAL_SERVER_ERROR,
    message: str = "Internal sever error",
    disconnect: str | None = None,
) -> None:
    await sio.emit(
        EnumSocketEvent.SOCKET_ERROR,
        {"status": status_code, "message": message},
        to=sid,
    )

    if disconnect:
        await sio.disconnect(sid)
        print(f"{RED}\U0001f480 disconnected because of error{RESET}")

    raise Exception(message)
