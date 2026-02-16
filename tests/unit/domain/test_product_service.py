from unittest.mock import AsyncMock
from decimal import Decimal
import pytest

from app.domain.models.product import Product
from app.domain.exceptions import ProductNotFoundError
from app.domain.services.product_service import ProductService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def service(mock_repo, mock_cache):
    mock_cache.get.return_value = None  # Simulate cache miss
    return ProductService(repo=mock_repo, cache=mock_cache)


@pytest.mark.asyncio
async def test_create_product_invalidates_cache(service, mock_repo, mock_cache):
    product = Product(name="Test", sku="SKU-001", price=Decimal("10.00"), stock=5)
    mock_repo.create.return_value = Product(
        id=1, name="Test", sku="SKU-001", price=Decimal("10.00"), stock=5
    )

    result = await service.create_product(product)

    assert result.id == 1
    mock_repo.create.assert_called_once_with(product)
    mock_cache.delete_pattern.assert_called_once_with("products:list:*")


@pytest.mark.asyncio
async def test_get_product_not_found_raises(service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(ProductNotFoundError):
        await service.get_product(999)  # Use an ID that doesn't exist


@pytest.mark.asyncio
async def test_get_product_cache_result(service, mock_repo, mock_cache):
    product = Product(id=1, name="Test", sku="SKU-001", price=Decimal("10.00"), stock=5)
    mock_cache.get.return_value = product  # Simulate cache hit

    result = await service.get_product(1)

    assert result == 1
    mock_cache.get.assert_called_once()
    assert mock_cache.set.call_args[0][0] == "product:1"  # Cache key should be correct


@pytest.mark.asyncio
async def test_get_product_returns_paginated(service, mock_repo, mock_cache):
    products = [
        Product(id=1, name=f"P{i}", sku=f"SKU-{i}", price=Decimal("10.00"), stock=5)
        for i in range(1, 4)
    ]
    mock_repo.get_all.return_value = products
    mock_repo.count.return_value = 3

    result, total = await service.get_products(skip=0, limit=20)

    assert len(result) == 3
    assert total == 3
