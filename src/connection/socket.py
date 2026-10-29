import socketio

from src.application import app
from src.connection.socket_server import sio
from src.socket.socket_handlers import register_socket_handlers

register_socket_handlers()

# The ASGI equivalent of http.createServer(app) with Socket.IO attached
main_server = socketio.ASGIApp(sio, other_asgi_app=app)

__all__ = ["main_server", "sio"]
