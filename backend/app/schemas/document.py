from datetime import datetime

from app.schemas import AppBaseModel


class DocumentResponse(AppBaseModel):
    id: str
    chat_id: str
    user_id: str
    filename: str
    content_type: str
    size_bytes: int
    is_indexed: bool
    created_at: datetime
