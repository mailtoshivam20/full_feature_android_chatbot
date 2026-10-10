import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_user

pytestmark = pytest.mark.asyncio


async def test_register(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "username": "newuser",
        "password": "Test1234",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "new@test.com"


async def test_register_duplicate_email(client: AsyncClient, db: AsyncSession):
    await make_user(db, email="dup@test.com")
    res = await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com",
        "username": "someone",
        "password": "Test1234",
    })
    assert res.status_code == 409


async def test_login_success(client: AsyncClient, db: AsyncSession):
    await make_user(db, email="login@test.com", password="Test1234")
    res = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com",
        "password": "Test1234",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_login_wrong_password(client: AsyncClient, db: AsyncSession):
    await make_user(db, email="badpw@test.com", password="Test1234")
    res = await client.post("/api/v1/auth/login", json={
        "email": "badpw@test.com",
        "password": "WrongPass1",
    })
    assert res.status_code == 401


async def test_get_me(client: AsyncClient, db: AsyncSession):
    user = await make_user(db, email="me@test.com")
    login = await client.post("/api/v1/auth/login", json={
        "email": "me@test.com",
        "password": "Test1234",
    })
    token = login.json()["access_token"]
    res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "me@test.com"


async def test_me_without_token(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
