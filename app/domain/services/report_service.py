import hashlib
import json

from app.core.logging import get_logger
from app.domain.ports.outbound.cache_port import CachePort
from app.domain.ports.outbound.product_repository_port import ProductRepositoryPort

logger = get_logger(__name__)


class ReportService:
    def __init__(self, product_repo: ProductRepositoryPort, cache: CachePort):
        self._product_repo = product_repo
        self._cache = cache

    async def get_top_products(self, limit: int = 10) -> list[dict]:
        cache_key = f"report:top_products:{limit}"
        cached = await self._cache.get(cache_key)
        if cached:
            logger.debug("report_cache_hit", report="top_products")
            return json.loads(cached)

        results = await self._product_repo.get_top_products(limit=limit)
        await self._cache.set(cache_key, json.dumps(results, default=str), ttl=600)
        logger.info("report_generated", report="top_products", items=len(results))
        return results

    async def get_sales_report(self, date_from: str, date_to: str) -> list[dict]:
        params = f"{date_from}:{date_to}"
        params_hash = hashlib.md5(params.encode()).hexdigest()[:8]
        cache_key = f"report:sales:{params_hash}"

        cached = await self._cache.get(cache_key)
        if cached:
            logger.debug("report_cache_hit", report="sales")
            return json.loads(cached)

        results = await self._product_repo.get_sales_report(date_from, date_to)
        await self._cache.set(cache_key, json.dumps(results, default=str), ttl=600)
        logger.info(
            "report_generated",
            report="sales",
            date_from=date_from,
            date_to=date_to,
            items=len(results),
        )
        return results
