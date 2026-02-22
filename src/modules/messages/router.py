from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from src.api import deps
from src.schemas.message import MessageCreate, MessageResponse, MessageList
from src.models.all_models import Message,  Conversation, ConversationParticipant, User

router = APIRouter()

@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    message_in: MessageCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Message:
    """
    Send a message to a conversation.
    """
    # 1. Validate conversation exists
    # 2. Validate sender is participant
    # 3. Fetch all participant IDs early
    # We can do this in a single query or two queries.
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    stmt_part = select(ConversationParticipant).where(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id
    )
    result_part = await db.execute(stmt_part)
    participant_record = result_part.scalars().first()
    
    if not participant_record:
        raise HTTPException(status_code=403, detail="You are not a participant of this conversation")

    # Fetch all participants of the conversation to broadcast 
    # (doing this before commit reduces post-commit DB reads)
    stmt_all_parts = select(ConversationParticipant.user_id).where(
        ConversationParticipant.conversation_id == conversation_id
    )
    parts_result = await db.execute(stmt_all_parts)
    participant_ids = [str(pid) for pid in parts_result.scalars().all()]

    # 4. Insert message
    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=message_in.content,
        message_type=message_in.message_type,
        media_url=message_in.media_url
    )
    db.add(message)
    
    # 5. Update conversation.updated_at
    from sqlalchemy.sql import func
    conversation.updated_at = func.now()
    
    # 6. Commit transaction
    await db.commit()
    await db.refresh(message)
    
    # 7. Publish event to PubSub (After successful commit)
    from src.core.pubsub import pubsub_manager
    msg_dict = MessageResponse.model_validate(message).model_dump(mode='json')
    try:
        await pubsub_manager.publish_message(msg_dict, participant_ids)
    except Exception as e:
        import logging
        logger = logging.getLogger("chat_api")
        logger.error(f"Failed to publish message event: {e}")
        # We don't fail the HTTP response if event publish fails, DB state is intact.
    
    return message

@router.get("/{conversation_id}/messages", response_model=MessageList)
async def list_messages(
    conversation_id: str,
    cursor: Optional[str] = Query(None, description="ISO timestamp of the last seen message for pagination"),
    limit: int = Query(20, le=100),
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> MessageList:
    """
    List messages in a conversation.
    Uses cursor-based pagination (backward from newest).
    """
    # Verify participation
    stmt = select(ConversationParticipant).where(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id == current_user.id
    )
    result = await db.execute(stmt)
    if not result.scalars().first():
        raise HTTPException(status_code=403, detail="You are not a participant of this conversation")

    # Query Messages
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(desc(Message.created_at))
    )
    
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Message.created_at < cursor_dt)
        except ValueError:
            pass # Ignore invalid cursor
            
    query = query.limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Calculate next cursor
    next_cursor = None
    if messages and len(messages) == limit:
        # The cursor for the next page is the created_at of the last item
        next_cursor = messages[-1].created_at.isoformat()
        
    return {"items": messages, "next_cursor": next_cursor}
