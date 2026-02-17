from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    sku: str = Field(..., min_length=1, max_length=50)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    stock: int = Field(..., ge=0)
    category: str = Field(default="", max_length=100)


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    sku: str
    price: Decimal
    stock: int
    category: str
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
