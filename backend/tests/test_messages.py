import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_chat, make_message, make_user

pytestmark = pytest.mark.asyncio


async def _auth_header(client: AsyncClient, email: str) -> dict:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "Test1234"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def test_list_messages_empty(client: AsyncClient, db: AsyncSession):
    user = await make_user(db, email="msg1@test.com")
    chat = await make_chat(db, user)
    headers = await _auth_header(client, "msg1@test.com")

    res = await client.get(f"/api/v1/chats/{chat.id}/messages/", headers=headers)
    assert res.status_code == 200
    assert res.json()["items"] == []


async def test_create_message(client: AsyncClient, db: AsyncSession):
    user = await make_user(db, email="msg2@test.com")
    chat = await make_chat(db, user)
    headers = await _auth_header(client, "msg2@test.com")

    res = await client.post(
        f"/api/v1/chats/{chat.id}/messages/",
        json={"content": "Hello world"},
        headers=headers,
    )
    assert res.status_code == 201
    assert res.json()["content"] == "Hello world"


async def test_soft_delete_message(client: AsyncClient, db: AsyncSession):
    user = await make_user(db, email="msg3@test.com")
    chat = await make_chat(db, user)
    msg = await make_message(db, chat, user, content="To delete")
    headers = await _auth_header(client, "msg3@test.com")

    res = await client.delete(f"/api/v1/chats/{chat.id}/messages/{msg.id}", headers=headers)
    assert res.status_code == 204

    # Should no longer appear in list
    res = await client.get(f"/api/v1/chats/{chat.id}/messages/", headers=headers)
    assert not any(m["id"] == msg.id for m in res.json()["items"])
