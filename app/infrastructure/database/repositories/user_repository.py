from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User
from app.domain.ports.outbound.user_repository_port import UserRepositoryPort
from app.infrastructure.database.models.user_model import UserModel


class UserRepository(UserRepositoryPort):
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            is_active=user.is_active,
        )
        self._db.add(model)
        await self._db.flush()
        await self._db.refresh(model)
        return _to_domain(model)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        model = result.scalars().first()
        return _to_domain(model) if model else None

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalars().first()
        return _to_domain(model) if model else None


def _to_domain(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        hashed_password=model.hashed_password,
        full_name=model.full_name,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
