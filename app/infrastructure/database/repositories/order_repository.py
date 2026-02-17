from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.order import Order, OrderItem, OrderStatus
from app.domain.ports.outbound.order_repository_port import OrderRepositoryPort
from app.infrastructure.database.models.order_model import OrderItemModel, OrderModel


class OrderRepository(OrderRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, order: Order) -> Order:
        model = OrderModel(
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            status=order.status.value,
            total_amount=order.total_amount,
            items=[
                OrderItemModel(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                )
                for item in order.items
            ],
        )
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return _to_domain(model)

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self._db.execute(
            select(OrderModel)
            .where(OrderModel.id == order_id)
            .options(selectinload(OrderModel.items))
        )
        model = result.scalars().first()
        return _to_domain(model) if model else None


def _to_domain(model: OrderModel) -> Order:
    return Order(
        id=model.id,
        customer_name=model.customer_name,
        customer_email=model.customer_email,
        status=OrderStatus(model.status),
        total_amount=model.total_amount,
        items=[
            OrderItem(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in model.items
        ],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
