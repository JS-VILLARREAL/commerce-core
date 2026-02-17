from app.core.logging import get_logger
from app.domain.exceptions import (
    InsufficientStockError,
    OrderNotFoundError,
    ProductNotFoundError,
    StockLockError,
)
from app.domain.models.order import Order, OrderStatus
from app.domain.ports.outbound.cache_port import CachePort
from app.domain.ports.outbound.order_repository_port import OrderRepositoryPort
from app.domain.ports.outbound.product_repository_port import ProductRepositoryPort

logger = get_logger(__name__)


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepositoryPort,
        product_repo: ProductRepositoryPort,
        cache: CachePort,
    ):
        self.order_repo = order_repo
        self._product_repo = product_repo
        self._cache = cache

    async def create_order(self, order: Order) -> Order:
        product_ids = sorted({item.product_id for item in order.items})
        acquired_locks: list[str] = []

        try:
            # Step 1: Acquire distributed locks (sorted to avoid deadlocks)
            for pid in product_ids:
                lock_key = f"lock:stock:{pid}"
                acquired = await self._cache.acquire_lock(lock_key, ttl=30)
                if not acquired:
                    raise StockLockError(pid)
                acquired_locks.append(lock_key)

            # Step 2: Validate stock and build items
            for item in order.items:
                product = await self._product_repo.get_by_id_for_update(item.product_id)
                if not product:
                    raise ProductNotFoundError(item.product_id)
                if not product.has_stock(item.quantity):
                    raise InsufficientStockError(
                        item.product_id, item.quantity, product.stock
                    )

                item.unit_price = product.price
                item.calculate_subtotal()
                product.decrease_stock(item.quantity)
                await self._product_repo.update_stock(product.id, product.stock)

            # Step 3: Calculate total and save
            order.status = OrderStatus.PENDING
            order.calculate_total()
            created = await self.order_repo.create(order)

            # Step 4: Invalidate caches
            await self._cache.delete_pattern("products:list:*")
            for pid in product_ids:
                await self._cache.delete(f"product:{pid}")
            await self._cache.delete_pattern("report:*")

            logger.info(
                "order_created", order_id=created.id, total=str(created.total_amount)
            )
            return created

        finally:
            for lock_key in acquired_locks:
                await self._cache.release_lock(lock_key)

    async def get_order(self, order_id: int) -> Order:
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id)
        return order
