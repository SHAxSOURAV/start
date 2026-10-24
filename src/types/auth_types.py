from typing import Literal, NotRequired, TypedDict

AppRole = Literal["USER", "DRIVER", "ADMIN", "SUPER_ADMIN"]


class AuthUserPayload(TypedDict):
    authId: str
    userId: str
    email: str
    role: str
    iat: NotRequired[int]
    exp: NotRequired[int]
