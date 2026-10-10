from __future__ import annotations

import chromadb
from chromadb import Collection

from app.core.config import get_settings

settings = get_settings()
_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client


def get_or_create_collection(chat_id: str) -> Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=f"chat_{chat_id.replace('-', '_')}",
        metadata={"hnsw:space": "cosine"},
    )


def delete_collection(chat_id: str) -> None:
    client = get_chroma_client()
    try:
        client.delete_collection(f"chat_{chat_id.replace('-', '_')}")
    except Exception:
        pass
