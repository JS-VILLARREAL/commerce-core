from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class Product:
    id: int | None = None
    name: str = ""
    description: str = ""
    sku: str = ""
    price: Decimal = Decimal("0")
    stock: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def has_stock(self, quantity: int) -> bool:
        return self.stock >= quantity

    def decrease_stock(self, quantity: int) -> None:
        if not self.has_stock(quantity):
            raise ValueError(f"Insufficient stock for product {self.id}")
        self.stock -= quantity
