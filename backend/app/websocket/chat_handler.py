import asyncio
import json
import uuid
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token, is_blocked
from app.models.chat import Chat, UserChat
from app.models.message import Message
from app.models.user import User
from app.services import ai_service
from app.services.rag_service import get_rag_augmented_messages
from app.services.title_service import generate_title


async def _authenticate(token: str) -> str | None:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None
    jti = payload.get("jti", "")
    if await is_blocked(jti):
        return None
    return payload.get("sub")


async def chat_websocket(websocket: WebSocket, chat_id: str, token: str) -> None:
    user_id = await _authenticate(token)
    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserChat).where(UserChat.chat_id == chat_id, UserChat.user_id == user_id)
        )
        if not result.scalar_one_or_none():
            await websocket.close(code=4003, reason="Forbidden")
            return

    await websocket.accept()
    stop_event = ai_service.get_stop_event(user_id, chat_id)
    stream_task: asyncio.Task | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid JSON"}))
                continue

            msg_type = data.get("type")

            if msg_type == "stop":
                stop_event.set()
                if stream_task and not stream_task.done():
                    stream_task.cancel()
                continue

            if msg_type != "message":
                continue

            content: str = data.get("content", "").strip()
            model: str = data.get("model", ai_service.DEFAULT_MODEL)
            if model not in ai_service.MODELS:
                model = ai_service.DEFAULT_MODEL

            if not content:
                continue

            # Reset stop event for new message
            stop_event.clear()

            async with AsyncSessionLocal() as db:
                # Persist user message
                user_msg = Message(
                    id=str(uuid.uuid4()),
                    chat_id=chat_id,
                    user_id=user_id,
                    role="user",
                    content=content,
                )
                db.add(user_msg)
                await db.commit()

                # Load chat for system prompt
                chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
                chat = chat_result.scalar_one_or_none()
                system_prompt = chat.system_prompt if chat else None

                # Load recent history (last 50 non-deleted messages)
                history_result = await db.execute(
                    select(Message)
                    .where(Message.chat_id == chat_id, Message.is_deleted == False)  # noqa: E712
                    .order_by(Message.created_at.desc())
                    .limit(50)
                )
                history = list(reversed(history_result.scalars().all()))

            raw_messages = [{"role": m.role, "content": m.content} for m in history]
            raw_messages = await get_rag_augmented_messages(chat_id, content, raw_messages)
            context_messages = ai_service.build_context_window(raw_messages, system_prompt, model)

            # Stream AI response
            ai_msg_id = str(uuid.uuid4())
            accumulated = []

            async def do_stream() -> None:
                nonlocal accumulated
                async for chunk in ai_service.stream_response(context_messages, model, stop_event):
                    accumulated.append(chunk)
                    await websocket.send_text(json.dumps({"type": "chunk", "delta": chunk}))

            stream_task = asyncio.create_task(do_stream())
            try:
                await stream_task
            except asyncio.CancelledError:
                pass

            full_content = "".join(accumulated)
            if full_content:
                async with AsyncSessionLocal() as db:
                    ai_msg = Message(
                        id=ai_msg_id,
                        chat_id=chat_id,
                        user_id=None,
                        role="assistant",
                        content=full_content,
                        model_used=model,
                        token_count=ai_service.count_tokens(full_content, model),
                    )
                    db.add(ai_msg)

                    # Update chat timestamp
                    chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
                    chat = chat_result.scalar_one_or_none()
                    if chat:
                        chat.updated_at = datetime.utcnow()

                    await db.commit()

                await websocket.send_text(json.dumps({"type": "done", "message_id": ai_msg_id}))

                # Auto-title on first message in a "New Chat"
                async with AsyncSessionLocal() as db:
                    chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
                    chat = chat_result.scalar_one_or_none()
                    if chat and chat.title == "New Chat":
                        asyncio.create_task(generate_title(chat_id, content))

    except WebSocketDisconnect:
        pass
    finally:
        ai_service.clear_stop_event(user_id, chat_id)
