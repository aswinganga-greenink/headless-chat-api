import json
import asyncio
import redis.asyncio as redis
from src.core.config import get_settings
from src.core.connection_manager import manager
import logging

settings = get_settings()
logger = logging.getLogger("chat_api")

class RedisPubSubManager:
    """
    Handles Redis connection and PubSub operations.
    This enables horizontal scaling by broadcasting events across all API instances.
    """
    def __init__(self):
        self.redis_conn = None
        self.pubsub = None
        self.channel_name = "chat_events"
        self._reader_task = None

    async def connect(self):
        self.redis_conn = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.pubsub = self.redis_conn.pubsub()
        await self.pubsub.subscribe(self.channel_name)
        logger.info("Connected to Redis PubSub")
        self._reader_task = asyncio.create_task(self.reader_task())

    async def disconnect(self):
        if self._reader_task:
            self._reader_task.cancel()
        if self.pubsub:
            await self.pubsub.unsubscribe(self.channel_name)
            await self.pubsub.close()
        if self.redis_conn:
            await self.redis_conn.aclose()
        logger.info("Disconnected from Redis PubSub")

    async def publish_message(self, message_data: dict, participant_ids: list[str]):
        """
        Publish a new message event to the Redis channel.
        message_data: dict representing the message (json serializable)
        participant_ids: list of string UUIDs to receive the message
        """
        payload = {
            "type": "new_message",
            "participant_ids": participant_ids,
            "data": message_data
        }
        await self.redis_conn.publish(self.channel_name, json.dumps(payload))

    async def reader_task(self):
        """
        Background task to read from Redis and broadcast to local WebSockets.
        """
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                    except json.JSONDecodeError:
                        continue
                        
                    if data.get("type") == "new_message":
                        p_ids = data.get("participant_ids", [])
                        msg_data = data.get("data", {})
                        
                        # Only send to active connections on THIS worker
                        for pid in p_ids:
                            await manager.send_personal_message(msg_data, pid)
                            
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Redis PubSub reader error: {e}")

pubsub_manager = RedisPubSubManager()
