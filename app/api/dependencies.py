from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services.product_service import ProductService
from app.domain.services.order_service import OrderService

from app.domain.services.report_service import ReportService
from app.infrastructure.cache.redis_cache_adapter import RedisCacheAdapter
from app.infrastructure.cache.redis_client import get_redis
from app.infrastructure.database.connection import get_db

from app.infrastructure.database.repositories.order_repository import OrderRepository
from app.infrastructure.database.repositories.product_repository import (
    ProductRepository,
)


async def get_cache_adapter() -> RedisCacheAdapter:
    redis = await get_redis()
    return RedisCacheAdapter(redis)


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
