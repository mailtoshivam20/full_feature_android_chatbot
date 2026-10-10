from openai import AsyncOpenAI

from app.core.config import get_settings
from app.models.chat import Chat
from app.core.database import AsyncSessionLocal

settings = get_settings()


async def generate_title(chat_id: str, first_message: str) -> None:
    """Background task: generate a short title for a new chat."""
    try:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Generate a concise, descriptive title (4-6 words) for a chat that starts with the following message. Reply with only the title, no punctuation.",
                },
                {"role": "user", "content": first_message[:500]},
            ],
            max_tokens=20,
            temperature=0.5,
        )
        title = response.choices[0].message.content.strip()
        if title:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                result = await db.execute(select(Chat).where(Chat.id == chat_id))
                chat = result.scalar_one_or_none()
                if chat and chat.title == "New Chat":
                    chat.title = title[:255]
                    await db.commit()
    except Exception:
        pass  # Title generation failure is silent
