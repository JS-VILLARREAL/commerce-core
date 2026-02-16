from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum


def _utcnow() -> datetime:
    return datetime.now(UTC)


class OrderStatus(StrEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


@dataclass
class OrderItem:
    id: int | None = None
    product_id: int = 0
    order_id: int | None = None
    quantity: int = 0
    unit_price: Decimal = Decimal("0")
    subtotal: Decimal = Decimal("0")

    def calculate_subtotal(self) -> None:
        self.subtotal = self.quantity * self.unit_price


@dataclass
class Order:
    id: int | None = None
    customer_name: str = ""
    customer_email: str = ""
    status: OrderStatus = OrderStatus.PENDING
    total_amount: Decimal = Decimal("0")
    items: list[OrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def calculate_total(self) -> None:
        self.total_amount = sum(item.subtotal for item in self.items)
