from __future__ import annotations

import asyncio
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_openai import OpenAIEmbeddings
from openai import AsyncOpenAI

from app.core.chroma_client import delete_collection, get_or_create_collection
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal

settings = get_settings()

_embeddings: OpenAIEmbeddings | None = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY,
        )
    return _embeddings


def _loader_for(path: str, content_type: str):
    if "pdf" in content_type:
        return PyPDFLoader(path)
    if "word" in content_type or "docx" in content_type or path.endswith(".docx"):
        return Docx2txtLoader(path)
    return TextLoader(path)


async def index_document(document_id: str) -> None:
    """Background task: chunk, embed, and upsert document into ChromaDB."""
    try:
        from sqlalchemy import select
        from app.models.document import Document

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if not doc:
                return

            loader = _loader_for(doc.storage_path, doc.content_type)
            pages = await asyncio.to_thread(loader.load)

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(pages)

        if not chunks:
            return

        texts = [c.page_content for c in chunks]
        ids = [f"{document_id}_{i}" for i in range(len(texts))]
        metadatas = [{"document_id": document_id, "chunk": i} for i in range(len(texts))]

        embeddings_fn = _get_embeddings()
        vectors = await asyncio.to_thread(embeddings_fn.embed_documents, texts)

        collection = get_or_create_collection(doc.chat_id)
        collection.upsert(ids=ids, embeddings=vectors, documents=texts, metadatas=metadatas)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.is_indexed = True
                await db.commit()

    except Exception:
        pass


async def retrieve_context(chat_id: str, query: str, k: int = 5) -> str:
    embeddings_fn = _get_embeddings()
    query_vector = await asyncio.to_thread(embeddings_fn.embed_query, query)

    collection = get_or_create_collection(chat_id)
    results = await asyncio.to_thread(
        lambda: collection.query(query_embeddings=[query_vector], n_results=k)
    )
    docs = results.get("documents", [[]])[0]
    if not docs:
        return ""
    return "\n\n---\n\n".join(docs)


async def has_indexed_documents(chat_id: str) -> bool:
    from sqlalchemy import select
    from app.models.document import Document

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(
                Document.chat_id == chat_id, Document.is_indexed == True  # noqa: E712
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None


async def get_rag_augmented_messages(
    chat_id: str,
    user_message: str,
    history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not await has_indexed_documents(chat_id):
        return history

    context = await retrieve_context(chat_id, user_message)
    if not context:
        return history

    rag_system = {
        "role": "system",
        "content": (
            "Use the following document excerpts to answer the user's question. "
            "If the answer is not in the documents, say so.\n\n"
            f"DOCUMENTS:\n{context}"
        ),
    }
    # Prepend RAG context after any existing system message
    augmented = []
    inserted = False
    for msg in history:
        if msg["role"] == "system" and not inserted:
            augmented.append(msg)
            augmented.append(rag_system)
            inserted = True
        else:
            augmented.append(msg)
    if not inserted:
        augmented.insert(0, rag_system)
    return augmented
