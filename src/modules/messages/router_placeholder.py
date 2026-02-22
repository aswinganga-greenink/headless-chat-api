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
    # ... Wait, I defined the route as /{conversation_id}/messages in the previous step content.
    # But in the file write I need to be careful.
    
    # Let's double check the previous file write content.
    # It was: @router.post("/{conversation_id}/messages", ...)
    # This implies the router is mounted at root or API root.
    # But wait, usually we want cleaner separation.
    # If I mount at /messages, the URL would be /messages/{conversation_id}/messages? No.
    
    # Let's stick to the previous file content which was correct for a top-level mount or properly prefixed.
    # Actually, the file was already written in step 465. I don't need to rewrite it unless I made a mistake.
    # Step 465 write_to_file was executed successfully.
    pass 
