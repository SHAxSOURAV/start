import json


def convert_to_array(data: str | list[str]) -> list[str]:
    return json.loads(data) if isinstance(data, str) else data
