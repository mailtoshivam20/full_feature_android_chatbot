from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    chat_id: str
    user_id: str
    filename: str
    content_type: str
    size_bytes: int
    is_indexed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
