from abc import ABC, abstractmethod
from app.domain.models.order import Order


class OrderRepositoryPort(ABC):
    @abstractmethod
    async def create(self, order: Order) -> Order: ...

    @abstractmethod
    async def get_by_id(self, order_id: int) -> Order | None: ...
