"""Helmet equivalent: the response headers helmet sets by default."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.config import config

BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "X-DNS-Prefetch-Control": "off",
    "X-Download-Options": "noopen",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Referrer-Policy": "no-referrer",
    "Origin-Agent-Cluster": "?1",
    "Cross-Origin-Opener-Policy": "same-origin",
    # Uploads are consumed cross-origin by frontend apps
    "Cross-Origin-Resource-Policy": "cross-origin",
    "Strict-Transport-Security": "max-age=15552000; includeSubDomains",
}

CSP = (
    "default-src 'self';base-uri 'self';font-src 'self' https: data:;"
    "form-action 'self';frame-ancestors 'self';img-src 'self' data:;"
    "object-src 'none';script-src 'self';script-src-attr 'none';"
    "style-src 'self' https: 'unsafe-inline';upgrade-insecure-requests"
)


async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)

    for key, value in BASE_HEADERS.items():
        response.headers[key] = value

    # Swagger UI (/docs, non-production) relies on inline scripts the
    # default CSP blocks; production keeps the full policy
    if config.env == "production":
        response.headers["Content-Security-Policy"] = CSP

    return response
