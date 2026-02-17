from decimal import Decimal
from unittest.mock import AsyncMock
import pytest
from app.domain.exceptions import (
    InsufficientStockError,
    ProductNotFoundError,
    StockLockError,
)
from app.domain.models.order import Order, OrderItem
from app.domain.models.product import Product
from app.domain.services.order_service import OrderService


@pytest.fixture
def mock_order_repo():
    return AsyncMock()


@pytest.fixture
def mock_product_repo():
    return AsyncMock()


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.acquire_lock.return_value = True
    return cache


@pytest.fixture
def service(mock_order_repo, mock_product_repo, mock_cache):
    return OrderService(
        order_repo=mock_order_repo, product_repo=mock_product_repo, cache=mock_cache
    )


def _make_product(product_id=1, stock=10, price="25.00"):
    return Product(
        id=product_id,
        name="Test",
        sku=f"SKU-{product_id}",
        price=Decimal(price),
        stock=stock,
    )


def _make_order(items=None):
    if items is None:
        items = [OrderItem(product_id=1, quantity=2)]
    return Order(
        customer_name="John Doe", customer_email="john@example.com", items=items
    )


@pytest.mark.asyncio
async def test_create_order_success(
    service, mock_product_repo, mock_order_repo, mock_cache
):
    mock_product_repo.get_by_id_for_update.return_value = _make_product(
        stock=10, price="25.00"
    )
    created = Order(
        id=1,
        customer_name="John Doe",
        customer_email="john@example.com",
        items=[
            OrderItem(
                id=1,
                order_id=1,
                product_id=1,
                quantity=2,
                unit_price=Decimal("25.00"),
                subtotal=Decimal("50.00"),
            )
        ],
        total_amount=Decimal("50.00"),
    )
    mock_order_repo.create.return_value = created

    result = await service.create_order(_make_order())

    assert result.id == 1
    mock_product_repo.update_stock.assert_called_once_with(1, 8)  # 10 - 2
    mock_cache.release_lock.assert_called()


@pytest.mark.asyncio
async def test_create_order_insufficient_stock(service, mock_product_repo):
    mock_product_repo.get_by_id_for_update.return_value = _make_product(stock=1)
    order = _make_order(items=[OrderItem(product_id=1, quantity=5)])

    with pytest.raises(InsufficientStockError):
        await service.create_order(order)


@pytest.mark.asyncio
async def test_create_order_product_not_found(service, mock_product_repo):
    mock_product_repo.get_by_id_for_update.return_value = None

    with pytest.raises(ProductNotFoundError):
        await service.create_order(_make_order())


@pytest.mark.asyncio
async def test_create_order_lock_failure(service, mock_cache):
    mock_cache.acquire_lock.return_value = False

    with pytest.raises(StockLockError):
        await service.create_order(_make_order())


@pytest.mark.asyncio
async def test_create_order_releases_locks_on_error(
    service, mock_product_repo, mock_cache
):
    mock_product_repo.get_by_id_for_update.side_effect = Exception("DB error")

    with pytest.raises(Exception, match="DB error"):
        await service.create_order(_make_order())

    mock_cache.release_lock.assert_called()  # Lock it ALLWAYS breaks free of locks
