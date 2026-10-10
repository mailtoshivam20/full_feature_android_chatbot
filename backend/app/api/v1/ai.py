from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.services import ai_service

router = APIRouter()


class ModelInfo(BaseModel):
    id: str
    display: str
    context_tokens: int


class GenerateRequest(BaseModel):
    chat_id: str
    model: str = ai_service.DEFAULT_MODEL


@router.get("/models", response_model=list[ModelInfo], summary="List available AI models")
async def list_models(current_user: User = Depends(get_current_active_user)):
    return [
        ModelInfo(id=model_id, display=info["display"], context_tokens=info["context_tokens"])
        for model_id, info in ai_service.MODELS.items()
    ]
