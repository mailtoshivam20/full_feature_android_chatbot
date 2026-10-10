from fastapi import APIRouter

from app.api.v1 import ai, auth, chats, export, files, messages, search, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(messages.router, prefix="/chats", tags=["messages"])
api_router.include_router(files.router, prefix="/chats", tags=["files"])
api_router.include_router(export.router, prefix="/chats", tags=["export"])
api_router.include_router(ai.router, prefix="", tags=["ai"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
