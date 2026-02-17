from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_report_service
from app.domain.models.user import User
from app.domain.services.report_service import ReportService
from app.schemas.report import SalesReportItem, TopProductItem

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/top-products", response_model=list[TopProductItem])
async def get_top_products(
    limit: int = Query(10, ge=1, le=50, description="Number of top products"),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """
    Get top-selling products ranked by total units sold.
    Results are cached in Redis with a 10-minute TTL.
    """
    return await service.get_top_products(limit=limit)


@router.get("/sales", response_model=list[SalesReportItem])
async def get_sales_report(
    date_from: str = Query(
        ...,
        alias="from",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Start date (YYYY-MM-DD)",
    ),
    date_to: str = Query(
        ...,
        alias="to",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="End date (YYYY-MM-DD)",
    ),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    """
    Get daily sales report for a date range.
    Results are cached in Redis with a 10-minute TTL.
    """
    return await service.get_sales_report(date_from, date_to)
