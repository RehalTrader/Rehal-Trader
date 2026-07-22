"""
Stripe-based subscription billing.

Flow:
  1. Frontend calls POST /billing/checkout-session -> redirected to Stripe Checkout.
  2. Stripe calls our webhook on successful payment -> we activate the Subscription row.
  3. Frontend calls GET /billing/portal-session for the customer to manage/cancel billing.

Requires env vars: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_ID_<PLAN>.
"""
import logging
from datetime import datetime, timedelta, timezone

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.subscription import Subscription
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

stripe.api_key = settings.STRIPE_SECRET_KEY

PRICE_ID_MAP = {
    "basic": settings.STRIPE_PRICE_ID_BASIC,
    "pro": settings.STRIPE_PRICE_ID_PRO,
    "enterprise": settings.STRIPE_PRICE_ID_ENTERPRISE,
}


@router.post("/checkout-session")
async def create_checkout_session(plan: str, current_user: User = Depends(get_current_user)):
    price_id = PRICE_ID_MAP.get(plan)
    if not price_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown plan '{plan}'")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            customer_email=current_user.email,
            client_reference_id=str(current_user.id),
            success_url=f"{settings.FRONTEND_URL}/dashboard?checkout=success",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard?checkout=cancelled",
            metadata={"user_id": str(current_user.id), "plan": plan},
        )
    except stripe.error.StripeError as exc:
        logger.error("Stripe checkout session creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment provider error") from exc

    return {"checkout_url": session.url}


@router.get("/portal-session")
async def create_portal_session(stripe_customer_id: str, current_user: User = Depends(get_current_user)):
    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/dashboard",
        )
    except stripe.error.StripeError as exc:
        logger.error("Stripe portal session creation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Payment provider error") from exc

    return {"portal_url": session.url}


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Verifies the Stripe signature before trusting the payload — never skip this in
    production, or anyone could POST a fake "payment succeeded" event.
    """
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        logger.warning("Invalid Stripe webhook signature: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature") from exc

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        user_id = session_obj["metadata"]["user_id"]
        plan_name = session_obj["metadata"]["plan"]
        await _activate_subscription(db, user_id, plan_name)

    elif event["type"] == "customer.subscription.deleted":
        session_obj = event["data"]["object"]
        user_id = session_obj.get("metadata", {}).get("user_id")
        if user_id:
            await _deactivate_subscription(db, user_id)

    return {"received": True}


async def _activate_subscription(db: AsyncSession, user_id: str, plan_name: str) -> None:
    import uuid
    from sqlalchemy import select

    from app.models.subscription import Plan
    from app.models.user import SubscriptionPlan

    user = await db.get(User, uuid.UUID(user_id))
    plan = await db.scalar(select(Plan).where(Plan.name == plan_name))
    if not user or not plan:
        logger.error("Cannot activate subscription — user or plan not found (%s / %s)", user_id, plan_name)
        return

    user.subscription_plan = SubscriptionPlan(plan_name)
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_active=True,
    )
    db.add_all([user, subscription])
    await db.commit()
    logger.info("Activated '%s' subscription for user %s", plan_name, user_id)


async def _deactivate_subscription(db: AsyncSession, user_id: str) -> None:
    import uuid

    from app.models.user import SubscriptionPlan

    user = await db.get(User, uuid.UUID(user_id))
    if user:
        user.subscription_plan = SubscriptionPlan.FREE
        db.add(user)
        await db.commit()
        logger.info("Deactivated subscription for user %s", user_id)
