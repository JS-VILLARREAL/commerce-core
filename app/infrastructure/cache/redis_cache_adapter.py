import redis.asyncio as redis
from app.core.logging import get_logger
from app.domain.ports.outbound.cache_port import CachePort

logger = get_logger(__name__)


class RedisCacheAdapter(CachePort):
    def __init__(self, client: redis.Redis):
        self._redis = client

    async def get(self, key: str) -> str | None:
        try:
            return await self._redis.get(key)
        except redis.RedisError as e:
            logger.warning("redis_get_error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        try:
            await self._redis.set(key, value, ex=ttl)
        except redis.RedisError as e:
            logger.warning("redis_set_error", key=key, error=str(e))

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except redis.RedisError as e:
            logger.warning("redis_delete_error", key=key, error=str(e))

    async def delete_pattern(self, pattern: str) -> None:
        try:
            async for key in self._redis.scan_iter(match=pattern):
                await self._redis.delete(key)
        except redis.RedisError as e:
            logger.warning("redis_delete_pattern_error", pattern=pattern, error=str(e))

    async def acquire_lock(self, key: str, ttl: int = 30) -> bool:
        try:
            return bool(await self._redis.set(key, "1", nx=True, ex=ttl))
        except redis.RedisError as e:
            logger.warning("redis_lock_error", key=key, error=str(e))
            return True  # Degrade gracefully

    async def release_lock(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except redis.RedisError as e:
            logger.warning("redis_unlock_error", key=key, error=str(e))

    async def increment(self, key: str, ttl: int | None = None) -> int:
        try:
            val = await self._redis.incr(key)
            if ttl is not None and val == 1:
                await self._redis.expire(key, ttl)
            return val
        except redis.RedisError as e:
            logger.warning("redis_incr_error", key=key, error=str(e))
            return 0
