from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.error_handler import ErrorHandlerMiddleware
from app.api.middleware.logging_middleware import LoggingMiddleware
from app.api.middleware.rate_limiter import RateLimiterMiddleware
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.infrastructure.cache.redis_client import close_redis, get_redis

settings = get_settings()
setup_logging(debug=settings.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await get_redis()
    yield
    # Shutdown
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware (order matters: outermost first)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimiterMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
