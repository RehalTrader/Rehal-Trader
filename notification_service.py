"""
Fan-out notifications for high-confidence signals across Telegram, email, and web push.
Each channel fails independently and logs its own error — one channel going down must
never block the others or crash signal generation.
"""
import logging

import httpx
from aiosmtplib import send as smtp_send
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def _format_message(payload: dict) -> str:
    return (
        f"{payload['direction']} — {payload['symbol']} ({payload['timeframe']})\n"
        f"Confidence: {payload['confidence']:.1f}%\n"
        f"Entry: {payload['entry_price']}  |  SL: {payload['stop_loss']}  |  TP: {payload['take_profit']}"
    )


async def send_telegram_alert(payload: dict) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": _format_message(payload)})
    except Exception as exc:  # noqa: BLE001
        logger.error("Telegram alert failed: %s", exc)


async def send_email_alert(payload: dict, recipient: str) -> None:
    if not settings.SMTP_HOST or not recipient:
        return
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = recipient
    message["Subject"] = f"[Signal] {payload['direction']} {payload['symbol']}"
    message.set_content(_format_message(payload))
    try:
        await smtp_send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Email alert failed: %s", exc)


async def send_push_alert(payload: dict, subscription_info: dict) -> None:
    if not settings.WEBPUSH_PRIVATE_KEY or not subscription_info:
        return
    try:
        from pywebpush import webpush

        webpush(
            subscription_info=subscription_info,
            data=_format_message(payload),
            vapid_private_key=settings.WEBPUSH_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{settings.SMTP_FROM}"},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Push alert failed: %s", exc)


async def notify_all_channels(payload: dict) -> None:
    """Broadcast-only Telegram alert here; per-user email/push are triggered from the
    subscriber list in a background job (see docs) so each user's own contact info is used."""
    await send_telegram_alert(payload)
