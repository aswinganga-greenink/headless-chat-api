from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MessageBase(BaseModel):
    content: str
    message_type: str = "text" # text, image, file
    media_url: Optional[str] = None

class MessageCreate(MessageBase):
    """
    Schema for sending a message.
    """
    pass

class MessageResponse(MessageBase):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    created_at: datetime
    is_deleted: bool
    
    class Config:
        from_attributes = True

class MessageList(BaseModel):
    items: List[MessageResponse]
    next_cursor: Optional[str] = None # For pagination (e.g. timestamp or ID of last item)
