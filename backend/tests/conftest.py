import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.user import User
from app.models.chat import Chat, UserChat
from app.models.message import Message
from main import app

# Use SQLite in-memory for tests (no MySQL needed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(setup_db) -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── Factories ────────────────────────────────────────────────────────────────

async def make_user(db: AsyncSession, email: str = None, password: str = "Test1234") -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=email or f"user_{uuid.uuid4().hex[:6]}@test.com",
        username=f"user_{uuid.uuid4().hex[:8]}",
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.flush()
    return user


async def make_chat(db: AsyncSession, user: User, title: str = "Test Chat") -> Chat:
    chat = Chat(id=str(uuid.uuid4()), title=title, created_by=user.id)
    db.add(chat)
    await db.flush()
    membership = UserChat(user_id=user.id, chat_id=chat.id, role="owner")
    db.add(membership)
    await db.flush()
    return chat


async def make_message(
    db: AsyncSession, chat: Chat, user: User, content: str = "Hello", role: str = "user"
) -> Message:
    msg = Message(
        id=str(uuid.uuid4()),
        chat_id=chat.id,
        user_id=user.id if role == "user" else None,
        role=role,
        content=content,
    )
    db.add(msg)
    await db.flush()
    return msg
