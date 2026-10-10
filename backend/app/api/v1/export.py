import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.exceptions import ForbiddenError
from app.models.chat import Chat, UserChat
from app.models.message import Message
from app.models.user import User

router = APIRouter()


@router.get("/{chat_id}/export", summary="Export chat history")
async def export_chat(
    chat_id: str,
    format: str = Query("json", pattern="^(json|pdf)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Chat).join(UserChat, UserChat.chat_id == Chat.id).where(
            Chat.id == chat_id, UserChat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise ForbiddenError("Chat not found")

    msgs_result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id, Message.is_deleted == False)  # noqa: E712
        .order_by(Message.created_at.asc())
    )
    messages = msgs_result.scalars().all()

    if format == "json":
        data = {
            "chat": {
                "id": chat.id,
                "title": chat.title,
                "created_at": chat.created_at.isoformat(),
                "exported_at": datetime.utcnow().isoformat(),
            },
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "model_used": m.model_used,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }
        return Response(
            content=json.dumps(data, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{chat.title[:50]}.json"'},
        )

    # PDF export
    try:
        import weasyprint
    except ImportError:
        from fastapi import HTTPException
        raise HTTPException(status_code=501, detail="PDF export not available")

    html = _render_html(chat, messages)
    pdf_bytes = weasyprint.HTML(string=html).write_pdf()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{chat.title[:50]}.pdf"'},
    )


def _render_html(chat, messages) -> str:
    rows = "".join(
        f'<div class="msg {m.role}"><span class="role">{m.role}</span>'
        f'<span class="time">{m.created_at.strftime("%Y-%m-%d %H:%M")}</span>'
        f'<p>{m.content.replace("<", "&lt;").replace(">", "&gt;")}</p></div>'
        for m in messages
    )
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body{{font-family:sans-serif;max-width:800px;margin:auto;padding:2em}}
  h1{{font-size:1.4em}} .msg{{margin:1em 0;padding:.8em;border-radius:6px}}
  .user{{background:#e8f4fd}} .assistant{{background:#f0fdf4}}
  .role{{font-weight:bold;text-transform:capitalize}} .time{{float:right;color:#888;font-size:.85em}}
  p{{margin:.5em 0 0}}
</style></head><body>
<h1>{chat.title}</h1>
<p>Exported: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</p>
{rows}
</body></html>"""
