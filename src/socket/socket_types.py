from typing import Any, TypedDict

from src.types.auth_types import AuthUserPayload


class SocketData(TypedDict):
    user: AuthUserPayload


class SendMessagePayload(TypedDict):
    receiverId: str
    chatId: str
    message: str


# Server -> client events: send_message, socket_error, online_status,
# update_location. Payloads are the emit_result envelope.
ServerToClientPayload = dict[str, Any]
