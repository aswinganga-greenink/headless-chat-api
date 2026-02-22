from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.database.base_class import Base

class Conversation(Base):
    """
    Represents a chat conversation (either 1:1 or group).
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=True) # Used for group chats
    is_group = Column(Boolean, default=False)
    
    # Optional metadata or state
    # last_message_at can be added later
    
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    creator = relationship("User", back_populates="created_conversations")
    participants = relationship(
        "ConversationParticipant", 
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    messages = relationship(
        "Message", 
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="desc(Message.created_at)"
    )
