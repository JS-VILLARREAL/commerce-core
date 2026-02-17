from unittest.mock import AsyncMock, patch

import pytest

from app.domain.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.domain.models.user import User
from app.domain.services.user_service import UserService


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return UserService(repo=mock_repo)


# ── register ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_success(service, mock_repo):
    mock_repo.get_by_email.return_value = None
    mock_repo.create.return_value = User(
        id=1, email="new@example.com", hashed_password="hashed", full_name="New User"
    )

    result = await service.register("new@example.com", "securepass", "New User")

    assert result.id == 1
    assert result.email == "new@example.com"
    mock_repo.get_by_email.assert_called_once_with("new@example.com")
    mock_repo.create.assert_called_once()
    created_user = mock_repo.create.call_args[0][0]
    assert created_user.email == "new@example.com"
    assert created_user.hashed_password != "securepass"  # must be hashed


@pytest.mark.asyncio
async def test_register_duplicate_email(service, mock_repo):
    mock_repo.get_by_email.return_value = User(
        id=1, email="dup@example.com", hashed_password="hashed", full_name="Existing"
    )

    with pytest.raises(UserAlreadyExistsError):
        await service.register("dup@example.com", "password123", "Dup User")


# ── authenticate ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_authenticate_success(service, mock_repo):
    mock_repo.get_by_email.return_value = User(
        id=1,
        email="user@example.com",
        hashed_password="$2b$12$placeholder",  # will be overridden by patch
        full_name="User",
    )

    with patch("app.domain.services.user_service.verify_password", return_value=True):
        token = await service.authenticate("user@example.com", "correctpass")

    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_authenticate_wrong_password(service, mock_repo):
    mock_repo.get_by_email.return_value = User(
        id=1,
        email="user@example.com",
        hashed_password="$2b$12$placeholder",
        full_name="User",
    )

    with patch("app.domain.services.user_service.verify_password", return_value=False):
        with pytest.raises(InvalidCredentialsError):
            await service.authenticate("user@example.com", "wrongpass")


@pytest.mark.asyncio
async def test_authenticate_user_not_found(service, mock_repo):
    mock_repo.get_by_email.return_value = None

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("nobody@example.com", "password")


@pytest.mark.asyncio
async def test_authenticate_inactive_user(service, mock_repo):
    mock_repo.get_by_email.return_value = User(
        id=1,
        email="inactive@example.com",
        hashed_password="$2b$12$placeholder",
        full_name="Inactive",
        is_active=False,
    )

    with pytest.raises(InvalidCredentialsError):
        await service.authenticate("inactive@example.com", "password")


# ── get_user_by_email ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_by_email_found(service, mock_repo):
    mock_repo.get_by_email.return_value = User(
        id=1, email="user@example.com", full_name="User"
    )

    result = await service.get_user_by_email("user@example.com")

    assert result is not None
    assert result.email == "user@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(service, mock_repo):
    mock_repo.get_by_email.return_value = None

    result = await service.get_user_by_email("missing@example.com")

    assert result is None
