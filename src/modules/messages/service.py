from typing import List, Optional, Tuple
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.message import MessageCreate, MessageResponse, MessageList
from src.modules.messages.repository import MessageRepository
from src.core.pubsub import pubsub_manager
import logging

logger = logging.getLogger("chat_api")

class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MessageRepository(db)

    async def send_message(self, conversation_id: str, sender_id: str, message_in: MessageCreate) -> MessageResponse:
        """
        Validates business rules and sends a message.
        """
        # 1. Validate conversation exists and is not archived
        conversation = await self.repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        if conversation.is_archived:
            raise HTTPException(status_code=403, detail="Cannot send messages to an archived conversation")

        # 2. Validate sender is an active participant
        participant = await self.repo.get_participant(conversation_id, sender_id)
        if not participant:
            raise HTTPException(status_code=403, detail="You are not a participant of this conversation")
            
        if not participant.is_active:
            raise HTTPException(status_code=403, detail="You have left this conversation and cannot send messages")

        # 3. Fetch all participant IDs early for broadcasting
        participant_ids = await self.repo.get_all_participant_ids(conversation_id)

        # 4. Insert message
        message = self.repo.create_message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=message_in.content,
            message_type=message_in.message_type,
            media_url=message_in.media_url
        )
        
        # 5. Update conversation.updated_at
        self.repo.touch_conversation(conversation)
        
        # 6. Commit transaction
        await self.db.commit()
        await self.db.refresh(message)
        
        msg_response = MessageResponse.model_validate(message)
        
        # 7. Publish event to PubSub
        try:
            await pubsub_manager.publish_message(msg_response.model_dump(mode='json'), participant_ids)
        except Exception as e:
            logger.error(f"Failed to publish message event: {e}")
            
        return msg_response

    async def list_messages(self, conversation_id: str, user_id: str, limit: int, cursor: Optional[str]) -> MessageList:
        """
        Validates membership and lists messages with cursor pagination.
        """
        # 1. Verify participation
        participant = await self.repo.get_participant(conversation_id, user_id)
        if not participant:
            raise HTTPException(status_code=403, detail="You are not a participant of this conversation")
            
        # Note: even if participant.is_active == False, they can still usually read past messages.

        # 2. Parse cursor
        cursor_dt = None
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor)
            except ValueError:
                pass # Ignore invalid cursor

        # 3. Fetch messages
        messages = await self.repo.get_messages_paginated(conversation_id, limit, cursor_dt)

        # 4. Calculate next cursor
        next_cursor = None
        if messages and len(messages) == limit:
            next_cursor = messages[-1].created_at.isoformat()
            
        return MessageList(
            items=[MessageResponse.model_validate(m) for m in messages],
            next_cursor=next_cursor
        )

    async def read_message(self, conversation_id: str, user_id: str, last_seen_message_id: str):
        """
        Updates the user's last seen message ID for a conversation.
        """
        participant = await self.repo.get_participant(conversation_id, user_id)
        if not participant:
            raise HTTPException(status_code=403, detail="You are not a participant of this conversation")
            
        import uuid
        participant.last_seen_message_id = uuid.UUID(last_seen_message_id) if last_seen_message_id else None
        await self.db.commit()
        return {"status": "ok"}

    async def soft_delete_message(self, conversation_id: str, sender_id: str, message_id: str):
        """
        Soft deletes a message. Only the sender can delete their own message.
        """
        # 1. Verify message exists and belongs to conversation
        message = await self.repo.get_message(message_id)
        if not message or str(message.conversation_id) != conversation_id:
            raise HTTPException(status_code=404, detail="Message not found in this conversation")
            
        # 2. Verify ownership
        if str(message.sender_id) != sender_id:
            raise HTTPException(status_code=403, detail="You can only delete your own messages")
            
        # 3. Verify it's not already deleted
        if message.is_deleted:
            raise HTTPException(status_code=400, detail="Message is already deleted")
            
        # Create payload before commit to avoid expired object access
        event_payload = {
            "event_type": "message_deleted",
            "message_id": str(message.id),
            "conversation_id": conversation_id
        }

        # 4. Perform soft delete
        message.is_deleted = True
        await self.db.commit()
        
        # We might want to broadcast a 'message_deleted' event to participants
        # so clients can remove it from their UI in real-time.
        # This is strictly optional for MVP but good for V2 completeness.
        participant_ids = await self.repo.get_all_participant_ids(conversation_id)
        try:
            await pubsub_manager.publish_message(event_payload, participant_ids)
        except Exception as e:
            logger.error(f"Failed to publish delete event: {e}")
            
        return {"status": "deleted"}
