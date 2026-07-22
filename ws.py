import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.cache.redis_client import redis_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/signals")
async def signals_websocket(websocket: WebSocket):
    """
    Clients connect here and receive every new signal the moment it's published
    to the `signals:live` Redis channel by the AI engine / signal service.
    """
    await websocket.accept()
    pubsub = await redis_client.subscribe()

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is not None:
                await websocket.send_text(message["data"])
            else:
                # Keep the connection alive / detect client disconnects promptly
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:  # noqa: BLE001
        logger.error("WebSocket error: %s", exc)
    finally:
        await pubsub.unsubscribe()
