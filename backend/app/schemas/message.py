from datetime import datetime

from pydantic import BaseModel


class MessageCreate(BaseModel):
    content: str
    role: str = "user"


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    user_id: str | None
    role: str
    content: str
    model_used: str | None
    token_count: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    cursor: str | None = None
    has_more: bool = False
