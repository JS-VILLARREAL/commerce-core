from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.domain.exceptions import (
    DomainError,
    InsufficientStockError,
    OrderNotFoundError,
    ProductNotFoundError,
    StockLockError,
)

logger = get_logger(__name__)

_ERROR_MAP: dict[type, int] = {
    ProductNotFoundError: 404,
    OrderNotFoundError: 404,
    InsufficientStockError: 409,
    StockLockError: 409,
}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except DomainError as e:
            status_code = _ERROR_MAP.get(type(e), 400)
            logger.warning(
                "domain_error",
                error_type=type(e).__name__,
                detail=str(e),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status_code,
                content={"detail": str(e)},
            )
        except Exception as e:
            logger.error(
                "unhandled_error",
                error_type=type(e).__name__,
                detail=str(e),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
