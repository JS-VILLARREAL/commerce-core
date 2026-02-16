import json

from app.core.logging import get_logger
from app.domain.exceptions import ProductNotFoundError
from app.domain.models.product import Product
from app.domain.ports.outbound.cache_port import CachePort
from app.domain.ports.outbound.product_repository_port import ProductRepositoryPort

logger = get_logger(__name__)


class ProductService:
    def __init__(self, repo: ProductRepositoryPort, cache: CachePort):
        self.repo = repo
        self.cache = cache

    async def create_product(self, product: Product) -> Product:
        created = await self.repo.create(product)
        await self.cache.delete_pattern(
            "products:list:*"
        )  # Invalidate product list cache
        logger.info("product_created", product_id=created.id, sku=created.sku)
        return created

    async def get_product(self, product_id: int) -> Product:
        cache_key = f"product:{product_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            data = json.loads(cached)
            return Product(**data)

        product = await self.repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id)

        await self.cache.set(
            cache_key, _serialize_product(product), ttl=300
        )  # Cache for 5 minutes
        return product

    async def get_products(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[Product], int]:
        cache_key = f"products:list:{skip}:{limit}"
        cached = await self.cache.get(cache_key)
        if cached:
            data = json.loads(cached)
            products = [Product(**p) for p in data["items"]]
            return products, data["total"]

        products = await self.repo.get_all(skip=skip, limit=limit)
        total = await self.repo.count()

        cache_data = json.dumps(
            {"items": [_product_to_dict(p) for p in products], "total": total}
        )
        await self.cache.set(cache_key, cache_data, ttl=120)
        return products, total


def _product_to_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "sku": p.sku,
        "price": str(p.price),
        "stock": p.stock,
        "category": p.category,
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _serialize_product(p: Product) -> str:
    return json.dumps(_product_to_dict(p))
