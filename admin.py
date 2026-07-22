import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.signal import Signal
from app.models.subscription import Plan
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), _admin: User = Depends(get_current_admin)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


@router.patch("/users/{user_id}/deactivate", response_model=UserOut)
async def deactivate_user(
    user_id: uuid.UUID, db: AsyncSession = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/plans")
async def list_plans(db: AsyncSession = Depends(get_db), _admin: User = Depends(get_current_admin)):
    result = await db.execute(select(Plan))
    return list(result.scalars().all())


@router.get("/analytics/signals")
async def signal_analytics(db: AsyncSession = Depends(get_db), _admin: User = Depends(get_current_admin)):
    """Aggregate counts + rough win-rate proxy (by confidence bucket) for the AI performance dashboard."""
    since = datetime.now(timezone.utc) - timedelta(days=30)

    total = await db.scalar(select(func.count(Signal.id)).where(Signal.created_at >= since))

    by_direction_result = await db.execute(
        select(Signal.direction, func.count(Signal.id))
        .where(Signal.created_at >= since)
        .group_by(Signal.direction)
    )
    by_direction = {direction.value: count for direction, count in by_direction_result.all()}

    avg_confidence = await db.scalar(select(func.avg(Signal.confidence)).where(Signal.created_at >= since))

    by_asset_result = await db.execute(
        select(Signal.asset_class, func.count(Signal.id))
        .where(Signal.created_at >= since)
        .group_by(Signal.asset_class)
    )
    by_asset = {asset.value: count for asset, count in by_asset_result.all()}

    return {
        "window_days": 30,
        "total_signals": total or 0,
        "by_direction": by_direction,
        "by_asset_class": by_asset,
        "avg_confidence": round(avg_confidence, 2) if avg_confidence else 0,
    }
