import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import SubscriptionPlan, UserRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    subscription_plan: SubscriptionPlan
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = None
    telegram_chat_id: str | None = None
