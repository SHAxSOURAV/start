"""Redis Cache & Resilience Suite (10 Golden Rules Aligned).

Provides:
- Distributed Mutex Lock (SETNX) to prevent Cache Stampedes (Thundering Herd)
- TTL Jitter to prevent Cache Avalanches
- Cache Penetration defense via short-lived Null Value caching
- Small payload serialization with safe non-blocking fallback
"""

import asyncio
import json
import random
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from src.connection.connect_redis import get_redis_client
from src.util.logger import error_logger

NULL_SENTINEL = "__CACHE_NULL_VALUE__"

# Lua script to release lock only if the token matches (atomic release)
_RELEASE_LOCK_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


def add_ttl_jitter(base_ttl: int, jitter_ratio: float = 0.1) -> int:
    """Rule 6 (Cache Avalanche Defense): Adds random jitter to TTL.

    Example: base_ttl=3600 with 10% jitter returns random seconds between 3240 and 3960.
    """
    if base_ttl <= 0:
        return base_ttl
    delta = int(base_ttl * max(0.01, min(jitter_ratio, 0.5)))
    return base_ttl + random.randint(-delta, delta)


@asynccontextmanager
async def distributed_lock(
    lock_name: str,
    timeout_seconds: int = 10,
    acquire_timeout: float = 5.0,
    retry_interval: float = 0.05,
) -> AsyncGenerator[bool]:
    """Rule 6 (Cache Stampede / Thundering Herd Defense): Distributed Mutex Lock.

    Uses atomic Redis `SET lock:{name} {token} NX EX {timeout_seconds}`.
    Yields True if acquired, or False if acquire_timeout expired.
    Automatically releases lock cleanly on exit using atomic token verification.
    """
    client = get_redis_client()
    lock_key = f"lock:{lock_name}"
    lock_token = f"{random.random()}:{asyncio.get_running_loop().time()}"
    acquired = False

    if client is not None:
        start_time = asyncio.get_running_loop().time()
        while (asyncio.get_running_loop().time() - start_time) < acquire_timeout:
            try:
                result = await client.set(
                    lock_key, lock_token, nx=True, ex=max(1, timeout_seconds)
                )
                if result:
                    acquired = True
                    break
            except Exception as exc:
                error_logger.error(f"Distributed lock acquisition error: {exc}")
                break
            await asyncio.sleep(retry_interval)
    else:
        # Graceful fallback: allow single execution if Redis is offline
        acquired = True

    try:
        yield acquired
    finally:
        if acquired and client is not None:
            try:
                await client.eval(_RELEASE_LOCK_LUA, 1, lock_key, lock_token)  # type: ignore[no-untyped-call]
            except Exception as exc:
                error_logger.error(f"Distributed lock release error: {exc}")


async def cached_get_or_set(
    cache_key: str,
    fetch_func: Callable[[], Any],
    base_ttl_seconds: int = 3600,
    cache_null: bool = True,
    null_ttl_seconds: int = 60,
    jitter_ratio: float = 0.1,
) -> Any:
    """Enterprise caching pattern with Stampede, Avalanche, and Penetration defense.

    - Namespace: Automatically prefixed as cache:{cache_key}
    - Cache Penetration: Stores NULL_SENTINEL for null_ttl_seconds when fetch_func returns None
    - Cache Avalanche: Adds jitter_ratio to TTL
    - Cache Stampede: Mutex lock on cache miss
    """
    client = get_redis_client()
    full_key = f"cache:{cache_key}"

    # 1. Fast Cache Read
    if client is not None:
        try:
            cached_val = await client.get(full_key)
            if cached_val is not None:
                if cached_val == NULL_SENTINEL:
                    return None
                return json.loads(cached_val)
        except Exception as exc:
            error_logger.error(f"Cache get error for {full_key}: {exc}")

    # 2. Mutex Lock on Cache Miss (Cache Stampede Defense)
    lock_id = f"cache_fetch:{cache_key}"
    async with distributed_lock(lock_id, timeout_seconds=10) as has_lock:
        # Re-check cache inside lock in case another worker already populated it
        if has_lock and client is not None:
            try:
                cached_val = await client.get(full_key)
                if cached_val is not None:
                    if cached_val == NULL_SENTINEL:
                        return None
                    return json.loads(cached_val)
            except Exception:
                pass

        # 3. Fetch from primary source
        result = (
            await fetch_func()
            if asyncio.iscoroutinefunction(fetch_func)
            else fetch_func()
        )

        # 4. Save to Cache
        if client is not None:
            try:
                if result is None:
                    if cache_null:
                        # Cache Penetration Defense
                        await client.setex(
                            full_key, max(1, null_ttl_seconds), NULL_SENTINEL
                        )
                else:
                    ttl_with_jitter = add_ttl_jitter(base_ttl_seconds, jitter_ratio)
                    serialized = json.dumps(result)
                    await client.setex(full_key, max(1, ttl_with_jitter), serialized)
            except Exception as exc:
                error_logger.error(f"Cache set error for {full_key}: {exc}")

        return result
