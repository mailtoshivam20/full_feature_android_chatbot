import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.middleware import RateLimitMiddleware
from app.websocket.chat_handler import chat_websocket

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure storage directories exist
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Set it in your .env file.")

    logger.info("startup", env=settings.APP_ENV, upload_dir=settings.UPLOAD_DIR)
    yield
    logger.info("shutdown")


app = FastAPI(
    title="ChatApp API",
    version="1.0.0",
    description="Full-featured AI chat application API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "auth", "description": "Registration, login, token management"},
        {"name": "chats", "description": "Chat CRUD, pin, archive"},
        {"name": "messages", "description": "Message history and management"},
        {"name": "files", "description": "File upload and RAG document management"},
        {"name": "ai", "description": "AI model listing and non-streaming generation"},
        {"name": "search", "description": "Full-text search across chats"},
        {"name": "export", "description": "Export chat history"},
        {"name": "users", "description": "User profile management"},
    ],
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.websocket("/ws/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str, token: str):
    await chat_websocket(websocket, chat_id, token)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
