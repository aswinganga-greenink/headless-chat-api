from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from src.schemas.user import UserResponse

class ConversationBase(BaseModel):
    title: Optional[str] = None
    is_group: bool = False

class ConversationCreate(ConversationBase):
    """
    Schema for creating a conversation.
    For direct chats (is_group=False), participants should contain exactly 1 other user ID.
    For group chats, it can contain multiple.
    """
    participant_ids: List[UUID]

class ConversationUpdate(BaseModel):
    title: Optional[str] = None

class ConversationAddParticipants(BaseModel):
    participant_ids: List[UUID]

class ConversationResponse(ConversationBase):
    id: UUID
    creator_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
    # We might want to return participants or last message here
    
    class Config:
        from_attributes = True

class ConversationDetail(ConversationResponse):
    """
    Detailed response including participants.
    """
    participants: List[UserResponse] = []
