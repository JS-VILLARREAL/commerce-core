from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=1000)


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=200)
    customer_email: EmailStr
    items: list[OrderItemCreate] = Field(..., min_length=1)


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    status: str
    total_amount: Decimal
    items: list[OrderItemResponse]
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
