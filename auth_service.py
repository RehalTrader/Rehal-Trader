import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.user import User

logger = logging.getLogger(__name__)


class AuthError(Exception):
    pass


async def register_user(db: AsyncSession, email: str, full_name: str, password: str) -> User:
    existing = await db.scalar(select(User).where(User.email == email))
    if existing:
        raise AuthError("An account with this email already exists.")

    user = User(email=email, full_name=full_name, hashed_password=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("New user registered: %s", email)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.hashed_password):
        raise AuthError("Invalid email or password.")
    if not user.is_active:
        raise AuthError("This account has been deactivated.")
    return user


def issue_tokens(user: User) -> tuple[str, str]:
    access = create_access_token(str(user.id), role=user.role.value)
    refresh = create_refresh_token(str(user.id))
    return access, refresh
