"""
Thin async Redis wrapper used for:
  - caching latest signal per symbol (fast dashboard reads)
  - pub/sub channel that the WebSocket endpoint subscribes to for live pushes
"""
import json
import logging
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

SIGNAL_CHANNEL = "signals:live"


class RedisClient:
    def __init__(self, url: str):
        self._pool = redis.from_url(url, decode_responses=True)

    async def set_json(self, key: str, value: dict, ex: int | None = None) -> None:
        await self._pool.set(key, json.dumps(value), ex=ex)

    async def get_json(self, key: str) -> dict | None:
        raw = await self._pool.get(key)
        return json.loads(raw) if raw else None

    async def publish_signal(self, payload: dict[str, Any]) -> None:
        await self._pool.publish(SIGNAL_CHANNEL, json.dumps(payload))

    async def subscribe(self, channel: str = SIGNAL_CHANNEL):
        pubsub = self._pool.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def ping(self) -> bool:
        try:
            return await self._pool.ping()
        except Exception as exc:  # noqa: BLE001
            logger.error("Redis ping failed: %s", exc)
            return False


redis_client = RedisClient(settings.REDIS_URL)
