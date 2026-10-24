"""CORS policy.

The Express version used an origin callback; CORSMiddleware takes a regex, so
the same three rules are expressed as one pattern. Requests without an Origin
header are unaffected either way.
"""

from typing import Any

allowed_origins: list[str] = ["https://www.example.com"]

allow_origin_regex = (
    r"^(https://www\.example\.com|http://10\.10\.20\..*|http://3\.76\.70.*)$"
)

cors_options: dict[str, Any] = {
    "allow_origin_regex": allow_origin_regex,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
