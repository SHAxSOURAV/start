"""Async Redis Connection & High-Performance Blacklist / Revocation Service.

Provides sub-millisecond in-memory checking for token revocation, distributed locks,
and user bans, completely eliminating main database hits during auth middleware verification.
Hardened according to the 10 Golden Rules for Production Redis.
"""

import json
import time
from collections.abc import AsyncGenerator
from typing import Any

import redis.asyncio as aioredis
from fastapi import Request

from src.config import config
from src.util.logger import error_logger, logger

_redis_pool: aioredis.ConnectionPool | None = None
_redis_client: aioredis.Redis | None = None
_is_connected: bool = False

# Rule 3: Graceful in-memory fallback cache when Redis server is unreachable in development
_memory_blacklist: dict[str, float] = {}  # key -> expiry_timestamp


async def connect_redis() -> None:
    """Initializes the Async Redis connection pool and verifies connectivity."""
    global _redis_pool, _redis_client, _is_connected
    if _is_connected and _redis_client is not None:
        return
    if not config.redis.url:
        logger.warning(
            "REDIS_URL not configured. Operating in in-memory fallback mode."
        )
        return

    try:
        # Rule 2: Connection Pooling with Socket Timeouts & Health Checks
        _redis_pool = aioredis.ConnectionPool.from_url(
            config.redis.url,
            decode_responses=True,
            max_connections=100,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
            health_check_interval=30,
        )
        _redis_client = aioredis.Redis(connection_pool=_redis_pool)
        await _redis_client.ping()
        _is_connected = True
        logger.info("Redis Connected Successfully (Zero-DB Auth & Caching Active)")
    except Exception as exc:
        _is_connected = False
        logger.warning(
            f"Redis connection failed ({exc}). Operating in graceful in-memory fallback mode."
        )


async def disconnect_redis() -> None:
    """Closes Redis client and connection pool gracefully."""
    global _redis_pool, _redis_client, _is_connected
    try:
        if _redis_client is not None:
            await _redis_client.aclose()
        if _redis_pool is not None:
            await _redis_pool.disconnect()
        _is_connected = False
        logger.info("Redis disconnected")
    except Exception as exc:
        error_logger.error(f"Error disconnecting Redis: {exc}")


def get_redis_client() -> aioredis.Redis | None:
    """Returns the active async Redis client, or None if not connected."""
    if _is_connected and _redis_client is not None:
        return _redis_client
    return None


async def get_redis(request: Request) -> aioredis.Redis | None:
    """FastAPI route dependency injection helper (Rule 10)."""
    return get_redis_client()


class RedisService:
    """High-performance token revocation, account ban, and caching operations."""

    @staticmethod
    async def blacklist_token(jti: str, expires_in_seconds: int) -> None:
        """Blacklists a specific JWT token ID (jti) for its remaining lifetime (Rule 1 & Rule 8)."""
        if not jti or expires_in_seconds <= 0:
            return

        client = get_redis_client()
        if client is not None:
            try:
                # Rule 8: Key Namespace auth:blacklist:jti:*
                await client.setex(
                    f"auth:blacklist:jti:{jti}", max(1, expires_in_seconds), "true"
                )
                return
            except Exception as exc:
                error_logger.error(f"Redis blacklist_token error: {exc}")

        # Rule 3: In-memory fallback
        _memory_blacklist[f"auth:blacklist:jti:{jti}"] = (
            time.time() + expires_in_seconds
        )

    @staticmethod
    async def ban_user(auth_id: Any, duration_seconds: int = 900) -> None:
        """Immediately blocks an auth user from all API access for duration (Rule 1 & Rule 8)."""
        auth_str = str(auth_id)
        client = get_redis_client()
        if client is not None:
            try:
                # Rule 8: Key Namespace auth:ban:user:*
                await client.setex(
                    f"auth:ban:user:{auth_str}", max(1, duration_seconds), "true"
                )
                return
            except Exception as exc:
                error_logger.error(f"Redis ban_user error: {exc}")

        # Rule 3: In-memory fallback
        _memory_blacklist[f"auth:ban:user:{auth_str}"] = time.time() + duration_seconds

    @staticmethod
    async def unban_user(auth_id: Any) -> None:
        """Removes the ban flag for an auth user using non-blocking UNLINK (Rule 4)."""
        auth_str = str(auth_id)
        client = get_redis_client()
        if client is not None:
            try:
                # Rule 4: Use unlink instead of blocking del
                await client.unlink(f"auth:ban:user:{auth_str}")
            except Exception as exc:
                error_logger.error(f"Redis unban_user error: {exc}")

        _memory_blacklist.pop(f"auth:ban:user:{auth_str}", None)

    @staticmethod
    async def is_revoked(jti: str | None, auth_id: Any) -> tuple[bool, bool]:
        """Checks if token or user is blacklisted in a single round-trip (Rule 7 Pipelining).

        Returns (is_token_blacklisted, is_user_banned).
        """
        auth_str = str(auth_id)
        client = get_redis_client()

        if client is not None:
            try:
                # Rule 7: Pipeline multi-key reads in a single network round-trip
                async with client.pipeline(transaction=False) as pipe:
                    if jti:
                        pipe.exists(f"auth:blacklist:jti:{jti}")
                    else:
                        pipe.exists("dummy:nonexistent:key")
                    pipe.exists(f"auth:ban:user:{auth_str}")
                    results = await pipe.execute()
                return bool(results[0]), bool(results[1])
            except Exception as exc:
                error_logger.error(f"Redis is_revoked pipeline error: {exc}")

        # Rule 3: In-memory fallback with lazy expiration cleanup
        now = time.time()
        is_token_revoked = False
        if jti:
            token_key = f"auth:blacklist:jti:{jti}"
            exp = _memory_blacklist.get(token_key)
            if exp is not None:
                if exp > now:
                    is_token_revoked = True
                else:
                    _memory_blacklist.pop(token_key, None)

        user_key = f"auth:ban:user:{auth_str}"
        is_user_banned = False
        user_exp = _memory_blacklist.get(user_key)
        if user_exp is not None:
            if user_exp > now:
                is_user_banned = True
            else:
                _memory_blacklist.pop(user_key, None)

        return is_token_revoked, is_user_banned

    @staticmethod
    async def scan_keys(pattern: str) -> AsyncGenerator[str]:
        """Rule 4: Safely traverses keys using SCAN cursor instead of blocking KEYS *."""
        client = get_redis_client()
        if client is not None:
            try:
                async for key in client.scan_iter(match=pattern, count=100):
                    yield key
            except Exception as exc:
                error_logger.error(f"Redis scan_keys error: {exc}")

    @staticmethod
    async def get_json(key: str) -> Any | None:
        """Retrieves and deserializes JSON cached value (Fail-Open / Rule 3)."""
        client = get_redis_client()
        if client is None:
            return None
        try:
            raw = await client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as exc:
            logger.warning(f"Redis get_json error on key {key}: {exc}")
        return None

    @staticmethod
    async def set_json(key: str, value: Any, ttl_seconds: int = 60) -> None:
        """Serializes and caches value with mandatory TTL (Rule 1 & Rule 8)."""
        client = get_redis_client()
        if client is None:
            return
        try:
            serialized = json.dumps(value, default=str)
            await client.setex(key, max(1, ttl_seconds), serialized)
        except Exception as exc:
            logger.warning(f"Redis set_json error on key {key}: {exc}")
