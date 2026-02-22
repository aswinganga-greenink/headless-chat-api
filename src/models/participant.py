from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database.base_class import Base

class ConversationParticipant(Base):
    """
    Association table/model linking users to conversations.
    """
    __tablename__ = "conversation_participants"

    # Composite primary key for membership uniqueness
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    role = Column(String, default="member") # e.g., 'admin', 'member'
    
    # Relationships
    user = relationship("User", back_populates="participations")
    conversation = relationship("Conversation", back_populates="participants")
