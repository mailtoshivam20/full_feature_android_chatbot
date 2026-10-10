# ChatApp — Full-Stack AI Chat Application

FastAPI + MySQL backend with a React web frontend. Android/iOS can use the same REST + WebSocket API later.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), Alembic, MySQL 8, Redis, OpenAI API, LangChain, ChromaDB
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Zustand, React Query
- **Infra**: Docker Compose (local dev)

---

## Quick Start

### 1. Clone and configure

```bash
cd full_feature_android_chatbot
cp .env.example .env
```

Edit `.env` — the minimum required:

```env
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=chatapp
MYSQL_USER=chatapp_user
MYSQL_PASSWORD=chatapp_password
SECRET_KEY=<generate a random 32+ char string>
OPENAI_API_KEY=sk-...
```

### 2. Start MySQL and Redis

```bash
docker-compose up -d mysql redis
```

### 3. Set up the backend

```bash
cd backend
pip install -r requirements.txt
```

Copy the backend env file:

```bash
cp .env.example .env
# Edit MYSQL_HOST to "localhost" (not "mysql") for local dev without Docker backend
```

Run migrations:

```bash
python -m alembic upgrade head
```

Start the API:

```bash
uvicorn main:app --reload
```

API docs: http://localhost:8000/docs

### 4. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## Running Tests

```bash
cd backend
pip install pytest pytest-asyncio aiosqlite
pytest -v
```

Tests use SQLite in-memory — no MySQL connection needed.

---

## Project Structure

```
backend/
  app/
    api/v1/          ← REST routers (auth, chats, messages, files, ai, search, export, users)
    models/          ← SQLAlchemy models
    schemas/         ← Pydantic schemas
    services/        ← AI, RAG, file, chat services
    core/            ← config, database, security, deps, pagination, middleware
    websocket/       ← WebSocket streaming handler
  alembic/           ← Migrations
  tests/             ← pytest suite
  main.py            ← FastAPI app entry point

frontend/
  src/
    api/             ← Axios client + typed API wrappers
    store/           ← Zustand stores (auth, chat, ui)
    hooks/           ← useWebSocket, useTheme, useTTS
    components/      ← ChatList, ChatWindow, MessageBubble, MessageInput, ...
    pages/           ← Login, Register, ChatPage, Settings, Profile
```

---

## API Overview

| Method | Path | Description |
|---|---|---|
| POST | /api/v1/auth/register | Register |
| POST | /api/v1/auth/login | Login |
| POST | /api/v1/auth/refresh | Refresh tokens |
| POST | /api/v1/auth/logout | Logout |
| GET | /api/v1/chats/ | List chats |
| POST | /api/v1/chats/ | Create chat |
| GET | /api/v1/chats/{id}/messages/ | Message history |
| POST | /api/v1/chats/{id}/files/ | Upload document |
| GET | /api/v1/models | Available AI models |
| GET | /api/v1/search/?q= | Search messages |
| GET | /api/v1/chats/{id}/export?format=json | Export chat |
| WS | /ws/chat/{id}?token= | Streaming AI responses |

---

## WebSocket Protocol

Connect: `ws://localhost:8000/ws/chat/{chat_id}?token=<access_token>`

**Send message:**
```json
{"type": "message", "content": "Hello", "model": "gpt-4o-mini"}
```

**Stop generation:**
```json
{"type": "stop"}
```

**Server events:**
```json
{"type": "chunk", "delta": "...text..."}
{"type": "done", "message_id": "uuid"}
{"type": "error", "detail": "..."}
```

---

## File Upload & RAG

1. Upload a PDF, TXT, or DOCX to a chat via `POST /api/v1/chats/{id}/files/`
2. The file is indexed asynchronously (ChromaDB + OpenAI embeddings)
3. Poll `GET /api/v1/chats/{id}/files/` until `is_indexed: true`
4. Subsequent chat messages will automatically retrieve relevant document context

---

## Adding a New Alembic Migration

```bash
cd backend
python -m alembic revision --autogenerate -m "describe your change"
python -m alembic upgrade head
```
