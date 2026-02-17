from pydantic import BaseModel


class TopProductItem(BaseModel):
    product_id: int
    product_name: str
    category: str
    total_sold: int
    total_revenue: float


class SalesReportItem(BaseModel):
    date: str
    total_orders: int
    total_units: int
    total_revenue: float
