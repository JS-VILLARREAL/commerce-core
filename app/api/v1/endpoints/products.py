import math

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_current_user, get_product_service
from app.domain.models.product import Product
from app.domain.models.user import User
from app.domain.services.product_service import ProductService
from app.schemas.common import PaginatedResponse
from app.schemas.product import ProductCreate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreate,
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
):
    """Create a new product."""
    product = Product(
        name=body.name,
        description=body.description,
        sku=body.sku,
        price=body.price,
        stock=body.stock,
        category=body.category,
    )
    created = await service.create_product(product)
    return _to_response(created)


@router.get("/", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
):
    """List products with pagination. Results are cached in Redis."""
    skip = (page - 1) * page_size
    products, total = await service.get_products(skip=skip, limit=page_size)
    return PaginatedResponse(
        items=[_to_response(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


def _to_response(p: Product) -> ProductResponse:
    return ProductResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        sku=p.sku,
        price=p.price,
        stock=p.stock,
        category=p.category,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )
