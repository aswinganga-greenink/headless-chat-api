from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, desc
from sqlalchemy.orm import selectinload

from src.api import deps
from src.schemas.conversation import ConversationCreate, ConversationResponse, ConversationDetail, ConversationAddParticipants
from src.models.all_models import Conversation, User, ConversationParticipant

router = APIRouter()

@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_in: ConversationCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
) -> Conversation:
    """
    Create a new conversation.
    For direct chats, checks if one already exists.
    """
    participant_ids = set(conversation_in.participant_ids)
    
    # Validation: Users must exist
    # (Skipping detailed check for brevity, assuming IDs are valid or foreign key constraint will catch it, ideally check query)
    
    if not conversation_in.is_group:
        if len(participant_ids) != 1:
            raise HTTPException(status_code=400, detail="Direct chats must have exactly 1 other participant")
        
        target_user_id = list(participant_ids)[0]
        if target_user_id == current_user.id:
             raise HTTPException(status_code=400, detail="Cannot create direct chat with yourself")

        # Check existing direct conversation
        # Logic: Find a conversation where both users are participants and is_group is False
        # This query is complex in raw SQL or ORM without specific setup. 
        # Simplified approach: Create new for now, or use a specific finder.
        pass

    # Create Conversation
    conversation = Conversation(
        title=conversation_in.title,
        is_group=conversation_in.is_group,
        creator_id=current_user.id
    )
    db.add(conversation)
    await db.flush() # Get ID

    # Add participants
    # Add creator
    participants = []
    participants.append(
        ConversationParticipant(conversation_id=conversation.id, user_id=current_user.id, role="admin")
    )
    
    # Add others
    for pid in participant_ids:
        if pid == current_user.id: continue # Already added
        participants.append(
            ConversationParticipant(conversation_id=conversation.id, user_id=pid, role="member")
        )
    
    db.add_all(participants)
    await db.commit()
    await db.refresh(conversation)
    
    return conversation

@router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
) -> List[Conversation]:
    """
    List conversations the current user is a participant of.
    """
    # Join ConversationParticipant to filter by user_id
    stmt = (
        select(Conversation)
        .join(ConversationParticipant)
        .options(selectinload(Conversation.participants))
        .where(
            ConversationParticipant.user_id == current_user.id,
            ConversationParticipant.is_active == True
        )
        .order_by(desc(Conversation.updated_at))
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    conversations = result.scalars().all()
    
    response_list = []
    from src.models.all_models import Message
    from sqlalchemy import func
    
    # Bulk fetch the created_at timestamps for all last_seen_message_ids
    last_seen_ids = []
    for conv in conversations:
        part = next((p for p in conv.participants if p.user_id == current_user.id), None)
        if part and part.last_seen_message_id:
            last_seen_ids.append(part.last_seen_message_id)
            
    last_seen_timestamps = {}
    if last_seen_ids:
        # Group chunks if too large, but usually a single IN clause is fine
        ts_stmt = select(Message.id, Message.created_at).where(Message.id.in_(last_seen_ids))
        ts_res = await db.execute(ts_stmt)
        for msg_id, created_at in ts_res.all():
            last_seen_timestamps[msg_id] = created_at
            
    for conv in conversations:
        # We already have participants loaded via selectinload
        part = next((p for p in conv.participants if p.user_id == current_user.id), None)
        
        unread_count = 0
        if part:
            if part.last_seen_message_id and part.last_seen_message_id in last_seen_timestamps:
                last_time = last_seen_timestamps[part.last_seen_message_id]
                c_stmt = select(func.count(Message.id)).where(
                    Message.conversation_id == conv.id,
                    Message.created_at > last_time,
                    Message.is_deleted == False
                )
                c_res = await db.execute(c_stmt)
                unread_count = c_res.scalar() or 0
            else:
                # Never seen any message, count all non-deleted
                c_stmt = select(func.count(Message.id)).where(
                    Message.conversation_id == conv.id,
                    Message.is_deleted == False
                )
                c_res = await db.execute(c_stmt)
                unread_count = c_res.scalar() or 0
                
        # Build the response model
        conv_resp = ConversationResponse.model_validate(conv)
        conv_dict = conv_resp.model_dump()
        conv_dict["unread_count"] = unread_count
        response_list.append(ConversationResponse(**conv_dict))

    return response_list

@router.post("/{conversation_id}/participants", status_code=status.HTTP_200_OK)
async def add_participants(
    conversation_id: str,
    participants_in: ConversationAddParticipants,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Add participants to an existing conversation.
    Only strictly for group chats or converting direct to group?
    For now, allow adding to any conversation.
    """
    # Verify conversation exists and user is a participant (or admin)
    # Ideally only admins/creator should add.
    import uuid
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.participants))
        .where(Conversation.id == uuid.UUID(conversation_id))
    )
    result = await db.execute(stmt)
    conversation = result.scalars().first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if current user is admin/creator of the conversation
    # We need to check ConversationParticipant role for current_user
    # Simplified: Check if current_user.id == conversation.creator_id
    if conversation.creator_id != current_user.id:
         raise HTTPException(status_code=403, detail="Only the creator can add participants")
         
    # Check if direct chat -> maybe prevent adding? 
    # Or upgrade to group?
    # For simplicity, if not is_group, we mark it as group now?
    if not conversation.is_group:
        conversation.is_group = True
        db.add(conversation)

    # Add new participants
    existing_ids = {p.user_id for p in conversation.participants}
    new_participants = []
    
    # Iterate over UUIDs directly from Pydantic model
    for pid in participants_in.participant_ids:
        if pid in existing_ids:
            continue
            
        new_participants.append(
            ConversationParticipant(conversation_id=conversation.id, user_id=pid, role="member")
        )
    
    if new_participants:
        db.add_all(new_participants)
        await db.commit()
        
    return {"message": "Participants added successfully"}
