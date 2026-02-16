from abc import ABC, abstractmethod


class CachePort(ABC):
    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 300) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def delete_pattern(self, pattern: str) -> None: ...

    @abstractmethod
    async def acquire_lock(self, key: str, ttl: int = 30) -> bool: ...

    @abstractmethod
    async def release_lock(self, key: str) -> None: ...

    @abstractmethod
    async def increment(self, key: str, ttl: int | None = None) -> int: ...
