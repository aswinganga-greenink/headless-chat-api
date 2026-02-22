from sqlalchemy import Column, String, Boolean, ForeignKey, Index, desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.database.base_class import Base

class Message(Base):
    """
    Represents a single message within a conversation.
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    content = Column(String, nullable=True) # Text content
    message_type = Column(String, default="text") # e.g., 'text', 'image', 'system'
    media_url = Column(String, nullable=True) # For attachments
    
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages")

# Explicit composite index for efficient cursor-based backward pagination
Index('ix_messages_conversation_id_created_at_desc', Message.conversation_id, desc(Message.created_at))
