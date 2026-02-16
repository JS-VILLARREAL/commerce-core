from decimal import Decimal
import pytest
from app.domain.models.product import Product
from app.domain.models.order import Order, OrderItem, OrderStatus


class TestProduct:
    def test_has_stock_sufficient(self):
        product = Product(id=1, stock=10)
        assert product.has_stock(5) is True

    def test_has_stock_insufficient(self):
        product = Product(id=1, stock=3)
        assert product.has_stock(5) is False

    def test_decrease_stock(self):
        product = Product(id=1, stock=10)
        product.decrease_stock(3)
        assert product.stock == 7

    def test_decrease_stock_insufficient_raises(self):
        product = Product(id=1, stock=3)
        with pytest.raises(ValueError, match="Insufficient stock"):
            product.decrease_stock(5)


class TestOrderItem:
    def test_calculate_subtotal(self):
        item = OrderItem(
            product_id=1,
            quantity=3,
            unit_price=Decimal("10.50"),
        )
        item.calculate_subtotal()
        assert item.subtotal == Decimal("31.50")


class TestOrder:
    def test_calculate_total(self):
        order = Order(
            customer_name="Test",
            customer_email="test@test.com",
            items=[
                OrderItem(
                    product_id=1,
                    quantity=2,
                    unit_price=Decimal("10.00"),
                    subtotal=Decimal("20.00"),
                ),
                OrderItem(
                    product_id=2,
                    quantity=1,
                    unit_price=Decimal("5.00"),
                    subtotal=Decimal("5.00"),
                ),
            ],
        )
        order.calculate_total()
        assert order.total_amount == Decimal("25.00")

    def test_default_status_is_pending(self):
        order = Order(customer_name="Test", customer_email="t@t.com")
        assert order.status == OrderStatus.PENDING
