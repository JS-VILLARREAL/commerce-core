class DomainError(Exception):
    """Base class for domain exceptions."""

    pass


class ProductNotFoundError(DomainError):
    def __init__(self, product_id: int):
        self.product_id = product_id
        super().__init__(f"Product with ID {product_id} not found.")


class OrderNotFoundError(DomainError):
    def __init__(self, order_id: int):
        self.order_id = order_id
        super().__init__(f"Order with ID {order_id} not found.")


class InsufficientStockError(DomainError):
    def __init__(self, product_id: int, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available
        super().__init__(
            f"Insufficient stock for product {product_id}:"
            f"requested {requested}, available {available}."
        )


class StockLockError(DomainError):
    def __init__(self, product_id: int):
        self.product_id = product_id
        super().__init__(
            f"Could not acquire lock for product {product_id}."
            f"Another operation is in process."
        )


class UserNotFoundError(DomainError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email {email} not found")


class UserAlreadyExistsError(DomainError):
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email {email} already exists")


class InvalidCredentialsError(DomainError):
    def __init__(self):
        super().__init__("Invalid email or password")
