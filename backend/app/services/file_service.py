import os
import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.models.document import Document
from app.schemas.document import DocumentResponse

settings = get_settings()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "image/png",
    "image/jpeg",
    "image/webp",
}

MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


async def upload_file(
    file: UploadFile,
    chat_id: str,
    user_id: str,
    db: AsyncSession,
) -> DocumentResponse:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(f"Unsupported file type: {file.content_type}")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise ValidationError(f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    dest_dir = os.path.join(settings.UPLOAD_DIR, user_id, chat_id)
    os.makedirs(dest_dir, exist_ok=True)

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "")[1]
    storage_path = os.path.join(dest_dir, f"{file_id}{ext}")

    with open(storage_path, "wb") as f:
        f.write(contents)

    doc = Document(
        id=file_id,
        chat_id=chat_id,
        user_id=user_id,
        filename=file.filename or "upload",
        content_type=file.content_type,
        storage_path=storage_path,
        size_bytes=len(contents),
        is_indexed=False,
    )
    db.add(doc)
    await db.flush()
    return DocumentResponse.model_validate(doc)


async def delete_file(document_id: str, user_id: str, db: AsyncSession) -> None:
    from sqlalchemy import select
    from app.core.chroma_client import delete_collection
    from app.core.exceptions import ForbiddenError

    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise ForbiddenError("Document not found")

    try:
        os.remove(doc.storage_path)
    except FileNotFoundError:
        pass

    await db.delete(doc)
