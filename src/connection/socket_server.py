"""The Socket.IO server instance.

Kept in its own module so the handler modules can emit without importing the
module that registers them.
"""

import socketio

from src.connection.socket_cors import socket_cors

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=socket_cors["origin"],
)
