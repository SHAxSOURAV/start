"""JSON-safe conversion of Mongo/Beanie values.

ObjectIds become strings and datetimes ISO strings, matching what Express
produced when it serialized Mongoose documents.
"""

from datetime import date, datetime
from typing import Any

from bson import ObjectId
from pydantic import BaseModel


def serialize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return serialize(value.model_dump(by_alias=True))
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): serialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(v) for v in value]
    return value
