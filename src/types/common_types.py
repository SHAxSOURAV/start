from typing import Any, NotRequired, TypedDict


class PaginationMeta(TypedDict):
    page: int
    limit: int
    total: int
    totalPage: int


class ApiResponse(TypedDict):
    statusCode: int
    success: bool
    message: NotRequired[str | None]
    meta: NotRequired[dict[str, Any] | PaginationMeta | None]
    data: NotRequired[Any]
    activationToken: NotRequired[str | None]
