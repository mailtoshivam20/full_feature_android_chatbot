import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_chat, make_user

pytestmark = pytest.mark.asyncio


async def _auth_header(client: AsyncClient, email: str) -> dict:
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": "Test1234"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


async def test_create_and_list_chat(client: AsyncClient, db: AsyncSession):
    await make_user(db, email="cl1@test.com")
    headers = await _auth_header(client, "cl1@test.com")

    res = await client.post("/api/v1/chats/", json={"title": "My Chat"}, headers=headers)
    assert res.status_code == 201
    chat_id = res.json()["id"]

    res = await client.get("/api/v1/chats/", headers=headers)
    assert res.status_code == 200
    assert any(c["id"] == chat_id for c in res.json()["items"])


async def test_delete_chat(client: AsyncClient, db: AsyncSession):
    user = await make_user(db, email="del1@test.com")
    chat = await make_chat(db, user)
    headers = await _auth_header(client, "del1@test.com")

    res = await client.delete(f"/api/v1/chats/{chat.id}", headers=headers)
    assert res.status_code == 204


async def test_other_user_cannot_access_chat(client: AsyncClient, db: AsyncSession):
    user_a = await make_user(db, email="a@test.com")
    await make_user(db, email="b@test.com")
    chat = await make_chat(db, user_a)

    headers_b = await _auth_header(client, "b@test.com")
    res = await client.get(f"/api/v1/chats/{chat.id}", headers=headers_b)
    assert res.status_code == 403


async def test_pin_and_unpin(client: AsyncClient, db: AsyncSession):
    user = await make_user(db, email="pin@test.com")
    chat = await make_chat(db, user)
    headers = await _auth_header(client, "pin@test.com")

    res = await client.post(f"/api/v1/chats/{chat.id}/pin", headers=headers)
    assert res.json()["is_pinned"] is True

    res = await client.post(f"/api/v1/chats/{chat.id}/unpin", headers=headers)
    assert res.json()["is_pinned"] is False
