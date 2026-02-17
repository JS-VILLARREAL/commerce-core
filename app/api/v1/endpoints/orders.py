from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_order_service
from app.domain.models.order import Order, OrderItem
from app.domain.models.user import User
from app.domain.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderItemResponse, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    current_user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """
    Create a new order.

    - Validates stock for each product
    - Acquires distributed locks to prevent race conditions
    - Decrements stock atomically
    - Calculates totals automatically
    """
    order = Order(
        customer_name=body.customer_name,
        customer_email=body.customer_email,
        items=[
            OrderItem(product_id=item.product_id, quantity=item.quantity)
            for item in body.items
        ],
    )
    created = await service.create_order(order)
    return _to_response(created)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
):
    """Get order by ID with all items."""
    order = await service.get_order(order_id)
    return _to_response(order)


def _to_response(o: Order) -> OrderResponse:
    return OrderResponse(
        id=o.id,
        customer_name=o.customer_name,
        customer_email=o.customer_email,
        status=o.status.value,
        total_amount=o.total_amount,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in o.items
        ],
        created_at=o.created_at,
        updated_at=o.updated_at,
    )
