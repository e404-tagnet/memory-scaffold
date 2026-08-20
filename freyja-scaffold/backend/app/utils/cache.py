from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from app.core.config import get_settings

settings = get_settings()


class Cache:
    """Simple Redis cache wrapper. Falls back to dict if Redis unavailable."""

    def __init__(self):
        self._local: dict[str, Any] = {}
        self._redis: redis.Redis | None = None
        self._try_redis = settings.redis_url.startswith("redis://")

    async def connect(self):
        if self._try_redis and not self._redis:
            try:
                self._redis = await redis.from_url(settings.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None

    async def get(self, key: str) -> str | None:
        if self._redis:
            return await self._redis.get(key)
        return self._local.get(key)

    async def set(self, key: str, value: str, ttl: int = 300):
        if self._redis:
            await self._redis.setex(key, ttl, value)
        else:
            self._local[key] = value

    async def delete(self, key: str):
        if self._redis:
            await self._redis.delete(key)
        else:
            self._local.pop(key, None)


_cache = Cache()


async def get_cache() -> Cache:
    await _cache.connect()
    return _cache
