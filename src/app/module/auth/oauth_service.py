import time
from typing import Any

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from starlette import status

from src.config import config
from src.error.api_error import ApiError

GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"

# In-memory JWKS cache with 2-hour TTL
_KEY_CACHE: dict[str, dict[str, Any]] = {
    "google": {"keys": {}, "expires_at": 0.0},
    "apple": {"keys": {}, "expires_at": 0.0},
}
CACHE_TTL = 7200.0  # 2 hours in seconds


async def _fetch_jwks(provider: str, url: str) -> dict[str, Any]:
    now = time.time()
    cache = _KEY_CACHE[provider]

    if cache["keys"] and now < cache["expires_at"]:
        return cache["keys"]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as err:
        # If fetch fails but we have stale cached keys, fall back to them
        if cache["keys"]:
            return cache["keys"]
        raise ApiError(
            status.BAD_GATEWAY,
            f"Failed to fetch public signing keys from {provider.capitalize()}: {err}",
        ) from err

    # Index keys by their 'kid'
    keys_by_kid = {key["kid"]: key for key in data.get("keys", []) if "kid" in key}
    _KEY_CACHE[provider] = {
        "keys": keys_by_kid,
        "expires_at": now + CACHE_TTL,
    }
    return keys_by_kid


async def _get_public_key(provider: str, url: str, kid: str | None) -> Any:
    if not kid:
        raise ApiError(status.BAD_REQUEST, "Malformed token header: missing 'kid'")

    keys = await _fetch_jwks(provider, url)
    key_data = keys.get(kid)

    # If key wasn't in cache, invalidate cache and re-fetch once in case of key rotation
    if not key_data:
        _KEY_CACHE[provider]["expires_at"] = 0.0
        keys = await _fetch_jwks(provider, url)
        key_data = keys.get(kid)

    if not key_data:
        raise ApiError(
            status.UNAUTHORIZED,
            f"Invalid token: {provider.capitalize()} public key not found for kid '{kid}'",
        )

    try:
        return RSAAlgorithm.from_jwk(key_data)
    except Exception as err:
        raise ApiError(
            status.UNAUTHORIZED,
            f"Failed to parse {provider.capitalize()} public RSA key: {err}",
        ) from err


async def verify_google_id_token(id_token: str) -> dict[str, Any]:
    """Cryptographically verifies a Google ID token against Google's public JWKS.

    Enforces RS256 signature verification, expiry, issuer, audience, and email_verified claim.
    Returns the verified profile payload.
    """
    if not id_token:
        raise ApiError(status.BAD_REQUEST, "Google ID token is required")

    try:
        unverified_header = jwt.get_unverified_header(id_token)
    except Exception as err:
        raise ApiError(status.BAD_REQUEST, f"Invalid token format: {err}") from err

    kid = unverified_header.get("kid")
    alg = unverified_header.get("alg", "RS256")
    if alg != "RS256":
        raise ApiError(
            status.BAD_REQUEST, f"Unsupported algorithm '{alg}', expected RS256"
        )

    public_key = await _get_public_key("google", GOOGLE_CERTS_URL, kid)

    decode_kwargs: dict[str, Any] = {
        "key": public_key,
        "algorithms": ["RS256"],
        "options": {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iss": True,
        },
    }

    # Verify audience (Web, Android, iOS Client IDs)
    if config.oauth.google_client_id:
        expected_audiences = [
            aud.strip()
            for aud in config.oauth.google_client_id.split(",")
            if aud.strip()
        ]
        if expected_audiences:
            decode_kwargs["audience"] = expected_audiences
    elif config.env == "production":
        raise ApiError(
            status.INTERNAL_SERVER_ERROR,
            "Google OAuth client ID is not configured on the server",
        )

    try:
        payload = jwt.decode(id_token, **decode_kwargs)
    except jwt.ExpiredSignatureError as err:
        raise ApiError(status.UNAUTHORIZED, "Google ID token has expired") from err
    except jwt.InvalidAudienceError as err:
        raise ApiError(
            status.UNAUTHORIZED, "Google ID token audience mismatch"
        ) from err
    except jwt.InvalidIssuerError as err:
        raise ApiError(status.UNAUTHORIZED, "Google ID token issuer mismatch") from err
    except Exception as err:
        raise ApiError(
            status.UNAUTHORIZED, f"Google token verification failed: {err}"
        ) from err

    # Verify issuer claim explicitly
    iss = payload.get("iss")
    if iss not in ("https://accounts.google.com", "accounts.google.com"):
        raise ApiError(status.UNAUTHORIZED, f"Invalid Google token issuer: {iss}")

    # Enforce email_verified claim (Strict Security Rule)
    email_verified = payload.get("email_verified")
    if email_verified is not True and email_verified != "true":
        raise ApiError(status.UNAUTHORIZED, "Google account email is not verified")

    sub = payload.get("sub")
    if not sub:
        raise ApiError(status.UNAUTHORIZED, "Google ID token missing 'sub' claim")

    email = payload.get("email")
    if not email:
        raise ApiError(
            status.BAD_REQUEST, "Google account did not provide an email address"
        )

    return {
        "email": email.strip().lower(),
        "name": payload.get("name") or email.split("@")[0],
        "googleId": sub,
        "picture": payload.get("picture"),
        "emailVerified": True,
    }


async def verify_apple_identity_token(identity_token: str) -> dict[str, Any]:
    """Cryptographically verifies an Apple Identity Token against Apple's public JWKS.

    Handles Apple Gotchas:
    1. Returns 'appleId' (sub claim) as the primary permanent identifier.
    2. Gracefully handles returning users where 'email' is absent from subsequent tokens.
    """
    if not identity_token:
        raise ApiError(status.BAD_REQUEST, "Apple identity token is required")

    try:
        unverified_header = jwt.get_unverified_header(identity_token)
    except Exception as err:
        raise ApiError(status.BAD_REQUEST, f"Invalid token format: {err}") from err

    kid = unverified_header.get("kid")
    alg = unverified_header.get("alg", "RS256")
    if alg != "RS256":
        raise ApiError(
            status.BAD_REQUEST, f"Unsupported algorithm '{alg}', expected RS256"
        )

    public_key = await _get_public_key("apple", APPLE_KEYS_URL, kid)

    decode_kwargs: dict[str, Any] = {
        "key": public_key,
        "algorithms": ["RS256"],
        "issuer": "https://appleid.apple.com",
        "options": {
            "verify_signature": True,
            "verify_exp": True,
            "verify_iss": True,
        },
    }

    # Verify audience (App Bundle ID / Services ID)
    if config.oauth.apple_client_id:
        expected_audiences = [
            aud.strip()
            for aud in config.oauth.apple_client_id.split(",")
            if aud.strip()
        ]
        if expected_audiences:
            decode_kwargs["audience"] = expected_audiences
    elif config.env == "production":
        raise ApiError(
            status.INTERNAL_SERVER_ERROR,
            "Apple OAuth client ID is not configured on the server",
        )

    try:
        payload = jwt.decode(identity_token, **decode_kwargs)
    except jwt.ExpiredSignatureError as err:
        raise ApiError(status.UNAUTHORIZED, "Apple identity token has expired") from err
    except jwt.InvalidAudienceError as err:
        raise ApiError(
            status.UNAUTHORIZED, "Apple identity token audience mismatch"
        ) from err
    except jwt.InvalidIssuerError as err:
        raise ApiError(
            status.UNAUTHORIZED, "Apple identity token issuer mismatch"
        ) from err
    except Exception as err:
        raise ApiError(
            status.UNAUTHORIZED, f"Apple token verification failed: {err}"
        ) from err

    sub = payload.get("sub")
    if not sub:
        raise ApiError(status.UNAUTHORIZED, "Apple identity token missing 'sub' claim")

    raw_email = payload.get("email")
    email = raw_email.strip().lower() if raw_email else None

    # In Apple identity tokens, email_verified can be boolean or string
    raw_verified = payload.get("email_verified")
    is_verified = (
        raw_verified is True
        or raw_verified == "true"
        or (email is not None and raw_verified is None)
    )

    return {
        "email": email,
        "appleId": sub,
        "emailVerified": is_verified,
        "isPrivateEmail": payload.get("is_private_email") in (True, "true"),
    }
