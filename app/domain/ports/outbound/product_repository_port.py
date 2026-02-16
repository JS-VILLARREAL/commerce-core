from abc import ABC, abstractmethod
from app.domain.models.product import Product


class ProductRepositoryPort(ABC):
    @abstractmethod
    async def create(self, product: Product) -> Product: ...

    @abstractmethod
    async def get_by_id(self, product_id: int) -> Product | None: ...

    @abstractmethod
    async def get_by_id_for_update(self, product_id: int) -> Product | None: ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Product]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def update_stock(self, product_id: int, new_stock: int) -> None: ...

    @abstractmethod
    async def get_top_products(self, limit: int = 10) -> list[dict]: ...

    @abstractmethod
    async def get_sales_report(self, date_from: str, date_to: str) -> list[dict]: ...
