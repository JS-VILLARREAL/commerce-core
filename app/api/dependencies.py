from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.domain.models.user import User
from app.domain.services.product_service import ProductService
from app.domain.services.order_service import OrderService
from app.domain.services.report_service import ReportService
from app.domain.services.user_service import UserService
from app.infrastructure.cache.redis_cache_adapter import RedisCacheAdapter
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.database.connection import get_db

from app.infrastructure.database.repositories.order_repository import OrderRepository
from app.infrastructure.database.repositories.product_repository import (
    ProductRepository,
)
from app.infrastructure.database.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_cache_adapter() -> RedisCacheAdapter:
    redis = await get_redis()
    return RedisCacheAdapter(redis)


async def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    repo = UserRepository(db)
    return UserService(repo=repo)


async def get_product_service(
    db: AsyncSession = Depends(get_db),
    cache: RedisCacheAdapter = Depends(get_cache_adapter),
) -> ProductService:
    repo = ProductRepository(db)
    return ProductService(repo=repo, cache=cache)


async def get_order_service(
    db: AsyncSession = Depends(get_db),
    cache: RedisCacheAdapter = Depends(get_cache_adapter),
) -> OrderService:
    product_repo = ProductRepository(db)
    order_repo = OrderRepository(db)
    return OrderService(
        order_repo=order_repo,
        product_repo=product_repo,
        cache=cache,
    )


async def get_report_service(
    db: AsyncSession = Depends(get_db),
    cache: RedisCacheAdapter = Depends(get_cache_adapter),
) -> ReportService:
    repo = ProductRepository(db)
    return ReportService(product_repo=repo, cache=cache)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    email = decode_access_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
