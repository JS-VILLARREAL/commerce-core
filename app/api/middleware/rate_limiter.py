from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.cache.redis_cache_adapter import RedisCacheAdapter

logger = get_logger(__name__)
settings = get_settings()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate:{client_ip}"

        try:
            redis = await get_redis()
            adapter = RedisCacheAdapter(redis)
            count = await adapter.increment(key, ttl=60)

            if count > settings.RATE_LIMIT_PER_MINUTE:
                logger.warning("rate_limit_exceeded", client_ip=client_ip, count=count)
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Try again later."},
                )
        except Exception:
            pass  # If Redis is down, allow the request through

        return await call_next(request)
