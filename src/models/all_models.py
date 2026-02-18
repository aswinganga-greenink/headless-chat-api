from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from src.database.base_class import Base

class User(Base):
    """
    User model representing a registered user in the system.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Relationships
    conversations_created = relationship("Conversation", back_populates="creator")
    messages = relationship("Message", back_populates="sender")
    # For many-to-many relationship with conversations
    conversation_associations = relationship("ConversationParticipant", back_populates="user")

class Conversation(Base):
    """
    Conversation model representing a chat thread (direct or group).
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=True) # Only for group chats
    is_group = Column(Boolean, default=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    creator = relationship("User", back_populates="conversations_created")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")

class ConversationParticipant(Base):
    """
    Association table for User <-> Conversation many-to-many relationship.
    Stores metadata like role, join date, etc.
    """
    __tablename__ = "conversation_participants"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role = Column(String, default="member") # admin, member
    
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", back_populates="conversation_associations")

class Message(Base):
    """
    Message model representing a single message in a conversation.
    """
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    message_type = Column(String, default="text") # text, image, file, system
    media_url = Column(String, nullable=True) # Quick link to media if applicable
    
    # For tracking edits/deletes
    is_deleted = Column(Boolean, default=False)
    
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages")
