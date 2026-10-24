from datetime import datetime

import pymongo
from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from src.util.base_document import TimestampedDocument


class LocationCoordinates(BaseModel):
    type: str = "Point"
    coordinates: list[float] = Field(default_factory=list)


class User(TimestampedDocument):
    authId: PydanticObjectId
    name: str
    email: str
    profile_image: str | None = None
    phoneNumber: str | None = None
    dateOfBirth: str | None = None
    address: str | None = None
    isOnline: bool | None = False
    isDeleted: bool | None = False
    deletedAt: datetime | None = None
    # Absent until a location is set -- a bare { type: "Point" } without
    # coordinates breaks the 2dsphere index
    locationCoordinates: LocationCoordinates | None = None

    class Settings:
        name = "users"
        indexes = [
            pymongo.IndexModel([("authId", pymongo.ASCENDING)]),
            pymongo.IndexModel([("email", pymongo.ASCENDING)]),
            pymongo.IndexModel(
                [("isDeleted", pymongo.ASCENDING), ("deletedAt", pymongo.ASCENDING)]
            ),
            # Geospatial queries on live location updates
            pymongo.IndexModel([("locationCoordinates", pymongo.GEOSPHERE)]),
        ]
