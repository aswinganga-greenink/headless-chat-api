"""
Aggregation module to expose all SQLAlchemy models.
This ensures Alembic's env.py can load `Base.metadata` with all tables registered simply by importing this file.
"""

from src.models.user import User
from src.models.conversation import Conversation
from src.models.participant import ConversationParticipant
from src.models.message import Message

__all__ = [
    "User",
    "Conversation",
    "ConversationParticipant",
    "Message"
]
