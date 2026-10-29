from typing import Any


def create_error_message(message: str, path: str = "") -> list[dict[str, Any]]:
    return [{"path": path, "message": message}]
