"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = postgresql.ENUM("user", "admin", name="userrole")
    subscription_plan = postgresql.ENUM("free", "basic", "pro", "enterprise", name="subscriptionplan")
    asset_class = postgresql.ENUM("forex", "gold", "crypto", "indices", name="assetclass")
    signal_direction = postgresql.ENUM(
        "STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL", name="signaldirection"
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="user"),
        sa.Column("subscription_plan", subscription_plan, nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("telegram_chat_id", sa.String(64), nullable=True),
        sa.Column("push_subscription", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("asset_class", asset_class, nullable=False),
        sa.Column("timeframe", sa.String(8), nullable=False),
        sa.Column("direction", signal_direction, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("entry_price", sa.Float, nullable=False),
        sa.Column("stop_loss", sa.Float, nullable=False),
        sa.Column("take_profit", sa.Float, nullable=False),
        sa.Column("features", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("candle_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_signals_symbol", "signals", ["symbol"])
    op.create_index("ix_signals_asset_class", "signals", ["asset_class"])

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column("price_monthly_usd", sa.Float, nullable=False, server_default="0"),
        sa.Column("max_symbols", sa.Integer, nullable=False, server_default="3"),
        sa.Column("signal_delay_minutes", sa.Integer, nullable=False, server_default="15"),
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("subscriptions")
    op.drop_table("plans")
    op.drop_table("signals")
    op.drop_table("users")

    postgresql.ENUM(name="signaldirection").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="assetclass").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="subscriptionplan").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="userrole").drop(op.get_bind(), checkfirst=True)
