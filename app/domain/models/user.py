from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class User:
    id: int | None = None
    email: str = ""
    hashed_password: str = ""
    full_name: str = ""
    is_active: bool = True
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
