from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import deps
from src.schemas.message import MessageCreate, MessageResponse, MessageList, MessageRead
from src.models.all_models import User
from src.modules.messages.service import MessageService
from src.api import deps

router = APIRouter()

@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    message_in: MessageCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> MessageResponse:
    """
    Send a message to a conversation.
    Delegates all business logic and transaction safety to the MessageService.
    """
    service = MessageService(db)
    return await service.send_message(conversation_id, str(current_user.id), message_in)

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
    Delegates membership validation and querying to MessageService.
    """
    service = MessageService(db)
    return await service.list_messages(conversation_id, str(current_user.id), limit, cursor)

@router.put("/{conversation_id}/messages/read", status_code=status.HTTP_200_OK)
async def mark_read(
    conversation_id: str,
    payload: MessageRead,

    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Mark messages up to the provided ID as read.
    """
    service = MessageService(db)
    return await service.read_message(conversation_id, str(current_user.id), str(payload.last_seen_message_id))

@router.delete("/{conversation_id}/messages/{message_id}", status_code=status.HTTP_200_OK)
async def delete_message(
    conversation_id: str,
    message_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Soft delete a message.
    """
    service = MessageService(db)
    return await service.soft_delete_message(conversation_id, str(current_user.id), message_id)
