from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatListResponse, ChatResponse, ChatUpdate
from app.services import chat_service

router = APIRouter()


@router.get("/", response_model=ChatListResponse, summary="List chats")
async def list_chats(
    search: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = Query(None),
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.list_chats(
        current_user.id, db, search=search, limit=limit, cursor=cursor, include_archived=include_archived
    )


@router.post("/", response_model=ChatResponse, status_code=201, summary="Create chat")
async def create_chat(
    data: ChatCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.create_chat(current_user.id, data, db)


@router.get("/{chat_id}", response_model=ChatResponse, summary="Get chat")
async def get_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.get_chat(chat_id, current_user.id, db)


@router.put("/{chat_id}", response_model=ChatResponse, summary="Update chat")
async def update_chat(
    chat_id: str,
    data: ChatUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.update_chat(chat_id, current_user.id, data, db)


@router.delete("/{chat_id}", status_code=204, summary="Delete chat")
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await chat_service.delete_chat(chat_id, current_user.id, db)


@router.post("/{chat_id}/pin", response_model=ChatResponse, summary="Pin chat")
async def pin_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.pin_chat(chat_id, current_user.id, True, db)


@router.post("/{chat_id}/unpin", response_model=ChatResponse, summary="Unpin chat")
async def unpin_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.pin_chat(chat_id, current_user.id, False, db)


@router.post("/{chat_id}/archive", response_model=ChatResponse, summary="Archive chat")
async def archive_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.archive_chat(chat_id, current_user.id, True, db)


@router.post("/{chat_id}/unarchive", response_model=ChatResponse, summary="Unarchive chat")
async def unarchive_chat(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await chat_service.archive_chat(chat_id, current_user.id, False, db)
