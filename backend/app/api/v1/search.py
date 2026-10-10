from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.chat import Chat, UserChat
from app.models.message import Message
from app.models.user import User

router = APIRouter()


class SearchResult(BaseModel):
    message_id: str
    chat_id: str
    chat_title: str
    excerpt: str
    role: str
    created_at: datetime


@router.get("/", response_model=list[SearchResult], summary="Search messages across chats")
async def search_messages(
    q: str = Query(..., min_length=1, max_length=200),
    scope: str | None = Query(None, description="Limit to a specific chat_id"),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Message, Chat.title.label("chat_title"))
        .join(Chat, Chat.id == Message.chat_id)
        .join(UserChat, UserChat.chat_id == Chat.id)
        .where(
            UserChat.user_id == current_user.id,
            Message.is_deleted == False,  # noqa: E712
        )
    )

    if scope:
        query = query.where(Message.chat_id == scope)

    # Try fulltext first; fall back to LIKE
    try:
        ft_query = query.where(
            text("MATCH(messages.content) AGAINST(:q IN BOOLEAN MODE)")
        ).params(q=f"{q}*")
        result = await db.execute(ft_query.limit(limit))
        rows = result.all()
        if not rows:
            raise Exception("empty")
    except Exception:
        like_query = query.where(Message.content.ilike(f"%{q}%")).limit(limit)
        result = await db.execute(like_query)
        rows = result.all()

    return [
        SearchResult(
            message_id=row.Message.id,
            chat_id=row.Message.chat_id,
            chat_title=row.chat_title,
            excerpt=row.Message.content[:200],
            role=row.Message.role,
            created_at=row.Message.created_at,
        )
        for row in rows
    ]
