import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import ForbiddenError
from app.core.pagination import decode_cursor, encode_cursor
from app.models.chat import UserChat
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageListResponse, MessageResponse

router = APIRouter()


async def _assert_chat_access(chat_id: str, user_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(UserChat).where(UserChat.chat_id == chat_id, UserChat.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise ForbiddenError("Chat not found or access denied")


@router.get("/{chat_id}/messages/", response_model=MessageListResponse, summary="List messages")
async def list_messages(
    chat_id: str,
    limit: int = Query(30, ge=1, le=100),
    cursor: str | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_access(chat_id, current_user.id, db)

    query = select(Message).where(
        Message.chat_id == chat_id, Message.is_deleted == False  # noqa: E712
    )
    if cursor:
        parsed = decode_cursor(cursor)
        if parsed:
            cur_dt, cur_id = parsed
            query = query.where(
                (Message.created_at < cur_dt) | ((Message.created_at == cur_dt) & (Message.id < cur_id))
            )

    query = query.order_by(Message.created_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    messages = result.scalars().all()

    has_more = len(messages) > limit
    messages = messages[:limit]
    messages_asc = list(reversed(messages))

    next_cursor = encode_cursor(messages[-1].created_at, messages[-1].id) if has_more and messages else None

    return MessageListResponse(
        items=[MessageResponse.model_validate(m) for m in messages_asc],
        cursor=next_cursor,
        has_more=has_more,
    )


@router.post("/{chat_id}/messages/", response_model=MessageResponse, status_code=201, summary="Create message")
async def create_message(
    chat_id: str,
    data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_access(chat_id, current_user.id, db)

    msg = Message(
        id=str(uuid.uuid4()),
        chat_id=chat_id,
        user_id=current_user.id,
        role=data.role,
        content=data.content,
    )
    db.add(msg)
    await db.flush()
    return MessageResponse.model_validate(msg)


@router.delete("/{chat_id}/messages/{message_id}", status_code=204, summary="Delete message")
async def delete_message(
    chat_id: str,
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_access(chat_id, current_user.id, db)

    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.chat_id == chat_id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise ForbiddenError("Message not found")
    msg.is_deleted = True


@router.get("/{chat_id}/messages/search", response_model=MessageListResponse, summary="Search messages in chat")
async def search_messages(
    chat_id: str,
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_access(chat_id, current_user.id, db)

    result = await db.execute(
        select(Message)
        .where(
            Message.chat_id == chat_id,
            Message.is_deleted == False,  # noqa: E712
            Message.content.ilike(f"%{q}%"),
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return MessageListResponse(items=[MessageResponse.model_validate(m) for m in messages])
