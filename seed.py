"""
Seed the database with default subscription plans and a bootstrap admin user.

Usage (inside the backend container):
    python -m app.db.seed
"""
import asyncio
import logging
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.subscription import Plan
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_PLANS = [
    {"name": "free", "price_monthly_usd": 0, "max_symbols": 3, "signal_delay_minutes": 60},
    {"name": "basic", "price_monthly_usd": 19, "max_symbols": 10, "signal_delay_minutes": 15},
    {"name": "pro", "price_monthly_usd": 49, "max_symbols": 30, "signal_delay_minutes": 0},
    {"name": "enterprise", "price_monthly_usd": 199, "max_symbols": 999, "signal_delay_minutes": 0},
]


async def seed_plans(session) -> None:
    for plan_data in DEFAULT_PLANS:
        existing = await session.scalar(select(Plan).where(Plan.name == plan_data["name"]))
        if existing:
            continue
        session.add(Plan(**plan_data))
        logger.info("Seeded plan: %s", plan_data["name"])
    await session.commit()


async def seed_admin_user(session) -> None:
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!")

    existing = await session.scalar(select(User).where(User.email == admin_email))
    if existing:
        logger.info("Admin user already exists: %s", admin_email)
        return

    admin = User(
        email=admin_email,
        full_name="Platform Admin",
        hashed_password=hash_password(admin_password),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    session.add(admin)
    await session.commit()
    logger.info("Seeded admin user: %s (change the password immediately!)", admin_email)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_plans(session)
        await seed_admin_user(session)


if __name__ == "__main__":
    asyncio.run(main())
