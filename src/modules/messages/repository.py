from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.sql import func
from src.models.all_models import Message, Conversation, ConversationParticipant

class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_participant(self, conversation_id: str, user_id: str) -> Optional[ConversationParticipant]:
        stmt = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_participant_ids(self, conversation_id: str) -> List[str]:
        stmt = select(ConversationParticipant.user_id).where(
            ConversationParticipant.conversation_id == conversation_id
        )
        result = await self.db.execute(stmt)
        return [str(pid) for pid in result.scalars().all()]

    def create_message(
        self, 
        conversation_id: str, 
        sender_id: str, 
        content: str, 
        message_type: str, 
        media_url: Optional[str]
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type,
            media_url=media_url
        )
        self.db.add(message)
        return message

    def touch_conversation(self, conversation: Conversation):
        conversation.updated_at = func.now()

    async def get_messages_paginated(
        self, 
        conversation_id: str, 
        limit: int, 
        cursor_dt: Optional[datetime] = None
    ) -> List[Message]:
        query = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.is_deleted == False
            )
            .order_by(desc(Message.created_at))
        )
        
        if cursor_dt:
            query = query.where(Message.created_at < cursor_dt)
            
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
