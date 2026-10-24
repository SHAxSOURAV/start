from typing import Any


def delete_falsy_field(obj: dict[str, Any]) -> dict[str, Any]:
    for key in list(obj.keys()):
        if not obj[key]:
            del obj[key]
    return obj
