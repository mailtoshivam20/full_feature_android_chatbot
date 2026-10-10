from datetime import datetime

from pydantic import BaseModel


class ChatCreate(BaseModel):
    title: str = "New Chat"
    system_prompt: str | None = None


class ChatUpdate(BaseModel):
    title: str | None = None
    system_prompt: str | None = None


class ChatResponse(BaseModel):
    id: str
    title: str
    system_prompt: str | None
    is_pinned: bool
    is_archived: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    last_message_preview: str | None = None
    message_count: int = 0

    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    items: list[ChatResponse]
    total: int
    cursor: str | None = None
