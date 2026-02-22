from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from src.api import deps
from src.schemas.message import MessageCreate, MessageResponse, MessageList
from src.models.all_models import Message,  Conversation, ConversationParticipant, User

router = APIRouter()

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    message_in: MessageCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Message:
    """
    Send a message to a conversation.
    Note: conversation_id is passed as query param or part of URL in main router?
    Wait, the router in main.py will likely be mounted at /conversations.
    But this is a separate router. It's better to mount it at root or under conversations.
    Common pattern: 
    POST /conversations/{id}/messages
    
    If we mount this router at /conversations, we need to handle the path prefix carefully.
    Let's assume this router is included in main.py.
    """
    pass 
