import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import tiktoken
from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()

MODELS = {
    "gpt-4o": {"display": "GPT-4o", "context_tokens": 128000},
    "gpt-4o-mini": {"display": "GPT-4o Mini", "context_tokens": 128000},
    "gpt-3.5-turbo": {"display": "GPT-3.5 Turbo", "context_tokens": 16385},
}
DEFAULT_MODEL = "gpt-4o-mini"


def get_client() -> AsyncOpenAI:
    if not settings.OPENAI_API_KEY:
        from app.core.exceptions import ServiceUnavailableError
        raise ServiceUnavailableError("OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def count_tokens(text: str, model: str = DEFAULT_MODEL) -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def build_context_window(
    messages: list[dict[str, Any]],
    system_prompt: str | None,
    model: str = DEFAULT_MODEL,
    max_response_tokens: int = 2048,
) -> list[dict[str, Any]]:
    model_info = MODELS.get(model, MODELS[DEFAULT_MODEL])
    max_ctx = model_info["context_tokens"]
    budget = int(max_ctx * 0.8) - max_response_tokens

    result: list[dict[str, Any]] = []
    if system_prompt:
        result.append({"role": "system", "content": system_prompt})
        budget -= count_tokens(system_prompt, model)

    # Walk from newest to oldest, fill within budget
    selected: list[dict[str, Any]] = []
    for msg in reversed(messages):
        tokens = count_tokens(msg["content"], model) + 4  # per-message overhead
        if budget - tokens < 0:
            break
        selected.append(msg)
        budget -= tokens

    result.extend(reversed(selected))
    return result


# Per (user_id, chat_id) stop events
_stop_events: dict[tuple[str, str], asyncio.Event] = {}


def get_stop_event(user_id: str, chat_id: str) -> asyncio.Event:
    key = (user_id, chat_id)
    if key not in _stop_events:
        _stop_events[key] = asyncio.Event()
    return _stop_events[key]


def clear_stop_event(user_id: str, chat_id: str) -> None:
    _stop_events.pop((user_id, chat_id), None)


async def stream_response(
    messages: list[dict[str, Any]],
    model: str = DEFAULT_MODEL,
    stop_event: asyncio.Event | None = None,
) -> AsyncGenerator[str, None]:
    client = get_client()
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        if stop_event and stop_event.is_set():
            await stream.close()
            break
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta
