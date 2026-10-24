import re
from datetime import datetime

import bcrypt
import pymongo
from beanie import Insert, before_event
from pydantic import field_validator

from src.config import config
from src.util.base_document import TimestampedDocument
from src.util.enum import EnumUserRole

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Projection used wherever an Auth document is returned to a client:
# the password is never part of a response
AUTH_PUBLIC_PROJECTION = {"password": 0}


class Auth(TimestampedDocument):
    name: str
    email: str
    password: str = ""
    role: str
    isVerified: bool | None = None
    isBlocked: bool | None = False
    isActive: bool | None = False
    isDeleted: bool | None = False
    deletedAt: datetime | None = None
    googleId: str | None = None
    appleId: str | None = None
    verificationCode: str | None = None
    verificationCodeExpire: datetime | None = None
    verificationAttempts: int | None = 0
    activationCode: str | None = None
    activationCodeExpire: datetime | None = None
    activationAttempts: int | None = 0
    passwordChangedAt: datetime | None = None
    failedLoginAttempts: int | None = 0
    lockUntil: datetime | None = None

    class Settings:
        name = "auths"
        indexes = [
            pymongo.IndexModel([("email", pymongo.ASCENDING)], unique=True),
            pymongo.IndexModel(
                [("isDeleted", pymongo.ASCENDING), ("deletedAt", pymongo.ASCENDING)]
            ),
            pymongo.IndexModel([("googleId", pymongo.ASCENDING)], sparse=True),
            pymongo.IndexModel([("appleId", pymongo.ASCENDING)], sparse=True),
        ]

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not EMAIL_REGEX.match(cleaned):
            raise ValueError("Please provide a valid email address")
        return cleaned

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: str) -> str:
        allowed = {
            EnumUserRole.USER,
            EnumUserRole.DRIVER,
            EnumUserRole.ADMIN,
            EnumUserRole.SUPER_ADMIN,
        }
        if value not in allowed:
            raise ValueError(f"`{value}` is not a valid enum value for path `role`.")
        return value

    @before_event(Insert)
    def _hash_password(self) -> None:
        """Mongoose pre("save") equivalent: hash a password that isn't hashed."""
        if not self.password or is_hashed(self.password):
            return
        self.password = hash_password(self.password)

    @staticmethod
    async def is_auth_exist(email: str) -> Auth | None:
        return await Auth.find_one({"email": email})

    @staticmethod
    async def is_password_matched(given_password: str, saved_password: str) -> bool:
        if not given_password or not saved_password:
            return False
        try:
            return bcrypt.checkpw(
                given_password.encode("utf-8"), saved_password.encode("utf-8")
            )
        except ValueError, TypeError:
            return False


def hash_password(plain: str) -> str:
    salt = bcrypt.gensalt(rounds=int(config.bcrypt_salt_rounds))
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def is_hashed(value: str) -> bool:
    return bool(value) and value.startswith(("$2a$", "$2b$", "$2y$"))
