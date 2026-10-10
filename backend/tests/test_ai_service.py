import pytest

from app.services.ai_service import build_context_window, count_tokens

pytestmark = pytest.mark.asyncio


def test_count_tokens_basic():
    count = count_tokens("Hello world")
    assert count > 0


def test_build_context_window_respects_budget():
    # Create a large history that exceeds the budget
    messages = [{"role": "user", "content": "x " * 500}] * 50
    result = build_context_window(messages, system_prompt=None, model="gpt-3.5-turbo")
    # Should be trimmed to fit within 80% of 16385 tokens minus 2048 response tokens
    assert len(result) < 50


def test_build_context_window_keeps_system_prompt():
    messages = [{"role": "user", "content": "hello"}]
    system = "You are a helpful assistant."
    result = build_context_window(messages, system_prompt=system, model="gpt-4o-mini")
    assert result[0]["role"] == "system"
    assert result[0]["content"] == system


def test_build_context_window_newest_messages_kept():
    messages = [{"role": "user", "content": f"message {i} " + "x " * 200} for i in range(20)]
    result = build_context_window(messages, system_prompt=None, model="gpt-3.5-turbo")
    contents = [m["content"] for m in result if m["role"] == "user"]
    # Newest messages (highest index) should be present
    assert any("message 19" in c for c in contents)
