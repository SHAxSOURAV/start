"""Numeric HTTP status codes, named as in the `http-status` package."""

from http import HTTPStatus


class _Status:
    OK = HTTPStatus.OK.value
    CREATED = HTTPStatus.CREATED.value
    NO_CONTENT = HTTPStatus.NO_CONTENT.value
    BAD_REQUEST = HTTPStatus.BAD_REQUEST.value
    UNAUTHORIZED = HTTPStatus.UNAUTHORIZED.value
    FORBIDDEN = HTTPStatus.FORBIDDEN.value
    NOT_FOUND = HTTPStatus.NOT_FOUND.value
    CONFLICT = HTTPStatus.CONFLICT.value
    TOO_MANY_REQUESTS = HTTPStatus.TOO_MANY_REQUESTS.value
    INTERNAL_SERVER_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR.value
    SERVICE_UNAVAILABLE = HTTPStatus.SERVICE_UNAVAILABLE.value


status = _Status()
