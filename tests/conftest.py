import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.ports.outbound.cache_port import CachePort
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models.base import Base

from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class FakeCacheAdapter(CachePort):
    """In-memory cache for testing without Redis."""

    def __init__(self):
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def delete_pattern(self, pattern: str) -> None:
        import fnmatch

        keys_to_delete = [k for k in self._store if fnmatch.fnmatch(k, pattern)]
        for k in keys_to_delete:
            del self._store[k]

    async def acquire_lock(self, key: str, ttl: int = 30) -> bool:
        if key in self._store:
            return False
        self._store[key] = "1"
        return True

    async def release_lock(self, key: str) -> None:
        self._store.pop(key, None)

    async def increment(self, key: str, ttl: int | None = None) -> int:
        val = int(self._store.get(key, "0")) + 1
        self._store[key] = str(val)
        return val


@pytest_asyncio.fixture
async def client(db_engine):
    session_factory = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    from app.api.dependencies import get_cache_adapter

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache_adapter] = FakeCacheAdapter

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
