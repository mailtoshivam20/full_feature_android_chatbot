import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), default="New Chat", nullable=False)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), default=lambda: datetime.now(UTC), onupdate=func.now(), nullable=False
    )

    members: Mapped[list["UserChat"]] = relationship("UserChat", back_populates="chat", lazy="select")
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="chat", lazy="select", order_by="Message.created_at"
    )
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="chat", lazy="select")


class UserChat(Base):
    __tablename__ = "user_chats"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    chat_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(
        Enum("owner", "member", name="user_chat_role"), default="owner", nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), default=lambda: datetime.now(UTC), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="chats")
    chat: Mapped["Chat"] = relationship("Chat", back_populates="members")
