from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.domain.models.user import User
from app.domain.ports.outbound.user_repository_port import UserRepositoryPort

logger = get_logger(__name__)


class UserService:
    def __init__(self, repo: UserRepositoryPort):
        self._repo = repo

    async def register(self, email: str, password: str, full_name: str) -> User:
        existing = await self._repo.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(email)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        created = await self._repo.create(user)
        logger.info("user_registered", user_id=created.id, email=created.email)
        return created

    async def authenticate(self, email: str, password: str) -> str:
        user = await self._repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError()

        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        token = create_access_token(subject=user.email)
        logger.info("user_authenticated", user_id=user.id, email=user.email)
        return token

    async def get_user_by_email(self, email: str) -> User | None:
        return await self._repo.get_by_email(email)
