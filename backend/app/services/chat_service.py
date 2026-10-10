import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination import decode_cursor, encode_cursor
from app.models.chat import Chat, UserChat
from app.models.message import Message
from app.schemas.chat import ChatCreate, ChatListResponse, ChatResponse, ChatUpdate


async def _get_chat_or_403(chat_id: str, user_id: str, db: AsyncSession) -> Chat:
    result = await db.execute(
        select(Chat).join(UserChat, UserChat.chat_id == Chat.id).where(
            Chat.id == chat_id, UserChat.user_id == user_id
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise ForbiddenError("Chat not found or access denied")
    return chat


async def _chat_to_response(chat: Chat, db: AsyncSession) -> ChatResponse:
    # Last non-deleted message preview
    last_msg_result = await db.execute(
        select(Message.content)
        .where(Message.chat_id == chat.id, Message.is_deleted == False)  # noqa: E712
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    last_content = last_msg_result.scalar_one_or_none()

    count_result = await db.execute(
        select(func.count(Message.id)).where(
            Message.chat_id == chat.id, Message.is_deleted == False  # noqa: E712
        )
    )
    count = count_result.scalar_one_or_none() or 0

    return ChatResponse(
        **{c.key: getattr(chat, c.key) for c in chat.__table__.columns},
        last_message_preview=last_content[:80] if last_content else None,
        message_count=count,
    )


async def create_chat(user_id: str, data: ChatCreate, db: AsyncSession) -> ChatResponse:
    chat = Chat(id=str(uuid.uuid4()), title=data.title, system_prompt=data.system_prompt, created_by=user_id)
    db.add(chat)
    await db.flush()
    await db.refresh(chat)

    membership = UserChat(user_id=user_id, chat_id=chat.id, role="owner")
    db.add(membership)
    await db.flush()

    return await _chat_to_response(chat, db)


async def list_chats(
    user_id: str,
    db: AsyncSession,
    search: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
    include_archived: bool = False,
) -> ChatListResponse:
    query = (
        select(Chat)
        .join(UserChat, UserChat.chat_id == Chat.id)
        .where(UserChat.user_id == user_id)
    )
    if not include_archived:
        query = query.where(Chat.is_archived == False)  # noqa: E712
    if search:
        query = query.where(Chat.title.ilike(f"%{search}%"))
    if cursor:
        parsed = decode_cursor(cursor)
        if parsed:
            cur_dt, cur_id = parsed
            query = query.where(
                (Chat.updated_at < cur_dt) | ((Chat.updated_at == cur_dt) & (Chat.id < cur_id))
            )

    query = query.order_by(Chat.is_pinned.desc(), Chat.updated_at.desc()).limit(limit + 1)
    result = await db.execute(query)
    chats = result.scalars().all()

    has_more = len(chats) > limit
    chats = chats[:limit]
    next_cursor = encode_cursor(chats[-1].updated_at, chats[-1].id) if has_more and chats else None

    total_result = await db.execute(
        select(func.count(Chat.id))
        .join(UserChat, UserChat.chat_id == Chat.id)
        .where(UserChat.user_id == user_id)
    )
    total = total_result.scalar_one_or_none() or 0

    items = [await _chat_to_response(c, db) for c in chats]
    return ChatListResponse(items=items, total=total, cursor=next_cursor)


async def get_chat(chat_id: str, user_id: str, db: AsyncSession) -> ChatResponse:
    chat = await _get_chat_or_403(chat_id, user_id, db)
    return await _chat_to_response(chat, db)


async def update_chat(chat_id: str, user_id: str, data: ChatUpdate, db: AsyncSession) -> ChatResponse:
    chat = await _get_chat_or_403(chat_id, user_id, db)
    if data.title is not None:
        chat.title = data.title
    if data.system_prompt is not None:
        chat.system_prompt = data.system_prompt
    chat.updated_at = datetime.utcnow()
    return await _chat_to_response(chat, db)


async def delete_chat(chat_id: str, user_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(UserChat).where(
            UserChat.chat_id == chat_id,
            UserChat.user_id == user_id,
            UserChat.role == "owner",
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise ForbiddenError("Only the chat owner can delete it")

    # Soft-delete messages
    msgs = await db.execute(select(Message).where(Message.chat_id == chat_id))
    for msg in msgs.scalars():
        msg.is_deleted = True

    chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = chat_result.scalar_one_or_none()
    if chat:
        await db.delete(chat)


async def pin_chat(chat_id: str, user_id: str, pinned: bool, db: AsyncSession) -> ChatResponse:
    chat = await _get_chat_or_403(chat_id, user_id, db)
    chat.is_pinned = pinned
    return await _chat_to_response(chat, db)


async def archive_chat(chat_id: str, user_id: str, archived: bool, db: AsyncSession) -> ChatResponse:
    chat = await _get_chat_or_403(chat_id, user_id, db)
    chat.is_archived = archived
    return await _chat_to_response(chat, db)
