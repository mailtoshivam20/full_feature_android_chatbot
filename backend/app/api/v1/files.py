import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import ForbiddenError
from app.models.chat import UserChat
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services import file_service
from app.services.rag_service import index_document

router = APIRouter()


async def _assert_chat_access(chat_id: str, user_id: str, db: AsyncSession) -> None:
    result = await db.execute(
        select(UserChat).where(UserChat.chat_id == chat_id, UserChat.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise ForbiddenError("Chat not found or access denied")


@router.post(
    "/{chat_id}/files/",
    response_model=DocumentResponse,
    status_code=202,
    summary="Upload file to chat (indexed asynchronously)",
)
async def upload_file(
    chat_id: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_access(chat_id, current_user.id, db)
    doc = await file_service.upload_file(file, chat_id, current_user.id, db)
    background_tasks.add_task(asyncio.coroutine(lambda: index_document(doc.id)))
    # Use create_task for true async background (BackgroundTasks runs after response)
    asyncio.create_task(index_document(doc.id))
    return doc


@router.get("/{chat_id}/files/", response_model=list[DocumentResponse], summary="List chat files")
async def list_files(
    chat_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_access(chat_id, current_user.id, db)
    result = await db.execute(
        select(Document).where(Document.chat_id == chat_id).order_by(Document.created_at.desc())
    )
    return [DocumentResponse.model_validate(d) for d in result.scalars()]


@router.delete("/{chat_id}/files/{document_id}", status_code=204, summary="Delete file")
async def delete_file(
    chat_id: str,
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await _assert_chat_access(chat_id, current_user.id, db)
    await file_service.delete_file(document_id, current_user.id, db)
