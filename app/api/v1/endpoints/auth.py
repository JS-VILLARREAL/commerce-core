from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user, get_user_service
from app.domain.models.user import User
from app.domain.services.user_service import UserService
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    body: UserRegister,
    service: UserService = Depends(get_user_service),
):
    """Register a new user."""
    user = await service.register(body.email, body.password, body.full_name)
    return _to_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    service: UserService = Depends(get_user_service),
):
    """Login and receive a JWT access token."""
    token = await service.authenticate(body.email, body.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
):
    """Get the current authenticated user."""
    return _to_response(current_user)


def _to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        is_active=u.is_active,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )
