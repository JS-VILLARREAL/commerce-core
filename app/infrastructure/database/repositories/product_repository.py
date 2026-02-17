from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.product import Product
from app.domain.ports.outbound.product_repository_port import ProductRepositoryPort
from app.infrastructure.database.models.order_model import OrderItemModel, OrderModel
from app.infrastructure.database.models.product_model import ProductModel


class ProductRepository(ProductRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, product: Product) -> Product:
        model = ProductModel(
            name=product.name,
            description=product.description,
            sku=product.sku,
            price=product.price,
            stock=product.stock,
            category=product.category,
            is_active=product.is_active,
        )
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return _to_domain(model)

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self._db.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        model = result.scalars().first()
        return _to_domain(model) if model else None

    async def get_by_id_for_update(self, product_id: int) -> Product | None:
        result = await self._db.execute(
            select(ProductModel).where(ProductModel.id == product_id).with_for_update()
        )
        model = result.scalars().first()
        return _to_domain(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 20) -> list[Product]:
        result = await self._db.execute(
            select(ProductModel)
            .where(ProductModel.is_active.is_(True))
            .order_by(ProductModel.id)
            .offset(skip)
            .limit(limit)
        )
        return [_to_domain(m) for m in result.scalars().all()]

    async def count(self) -> int:
        result = await self._db.execute(
            select(func.count(ProductModel.id)).where(ProductModel.is_active.is_(True))
        )
        return result.scalar_one()

    async def update_stock(self, product_id: int, new_stock: int) -> None:
        await self._db.execute(
            update(ProductModel)
            .where(ProductModel.id == product_id)
            .values(stock=new_stock)
        )
        await self._db.flush()

    async def get_top_products(self, limit: int = 10) -> list[dict]:
        query = (
            select(
                ProductModel.id,
                ProductModel.name,
                ProductModel.category,
                func.sum(OrderItemModel.quantity).label("total_sold"),
                func.sum(OrderItemModel.subtotal).label("total_revenue"),
            )
            .join(OrderItemModel, OrderItemModel.product_id == ProductModel.id)
            .join(OrderModel, OrderModel.id == OrderItemModel.order_id)
            .where(OrderModel.status != "CANCELLED")
            .group_by(ProductModel.id, ProductModel.name, ProductModel.category)
            .order_by(func.sum(OrderItemModel.quantity).desc())
            .limit(limit)
        )
        result = await self._db.execute(query)
        return [
            {
                "product_id": row.id,
                "product_name": row.name,
                "category": row.category,
                "total_sold": int(row.total_sold),
                "total_revenue": float(row.total_revenue),
            }
            for row in result.all()
        ]

    async def get_sales_report(self, date_from: str, date_to: str) -> list[dict]:
        d_from = date.fromisoformat(date_from)  # "2026-02-14" -> date
        d_to = date.fromisoformat(date_to)

        day = func.date(OrderModel.created_at)

        query = (
            select(
                day.label("date"),
                func.count(func.distinct(OrderModel.id)).label("total_orders"),
                func.sum(OrderItemModel.quantity).label("total_units"),
                func.sum(OrderItemModel.subtotal).label("total_revenue"),
            )
            .join(OrderItemModel, OrderModel.id == OrderItemModel.order_id)
            .where(
                OrderModel.status != "CANCELLED",
                day >= d_from,
                day <= d_to,
            )
            .group_by(day)
            .order_by(day)
        )
        result = await self._db.execute(query)
        return [
            {
                "date": str(row.date),
                "total_orders": int(row.total_orders),
                "total_units": int(row.total_units),
                "total_revenue": float(row.total_revenue),
            }
            for row in result.all()
        ]


def _to_domain(model: ProductModel) -> Product:
    return Product(
        id=model.id,
        name=model.name,
        description=model.description,
        sku=model.sku,
        price=model.price,
        stock=model.stock,
        category=model.category,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
