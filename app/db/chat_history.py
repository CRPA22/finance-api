"""
Repositorio de historial de chat. Usa la BD de chat.
"""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.chat_models import ChatMessage, ChatSession
from app.core.logging_config import get_logger

logger = get_logger("chat_history")


async def get_chat_history(
    chat_db: AsyncSession,
    session_id: UUID,
    limit: int = 20,
) -> list[ChatMessage]:
    """Obtiene los últimos N mensajes de una sesión, ordenados por created_at ASC."""
    logger.debug("get_chat_history session_id=%s limit=%s", session_id, limit)
    result = await chat_db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def save_message(
    chat_db: AsyncSession,
    session_id: UUID,
    role: str,
    content: str,
) -> None:
    """Guarda un mensaje en el historial y hace commit."""
    logger.debug("save_message session_id=%s role=%s", session_id, role)
    msg = ChatMessage(session_id=session_id, role=role, content=content)
    chat_db.add(msg)
    await chat_db.commit()


async def list_chats(chat_db: AsyncSession) -> list[dict]:
    """Lista conversaciones con session_id, title y updated_at. Ordenadas por updated_at DESC."""
    result = await chat_db.execute(
        select(ChatSession)
        .order_by(ChatSession.updated_at.desc())
    )
    rows = result.scalars().all()
    return [
        {"session_id": s.session_id, "title": s.title, "updated_at": s.updated_at}
        for s in rows
    ]


async def create_or_update_session_title(
    chat_db: AsyncSession,
    session_id: UUID,
    title: str,
) -> None:
    """Inserta o actualiza el título de una sesión (upsert)."""
    stmt = pg_insert(ChatSession).values(
        session_id=session_id,
        title=title[:200],
        updated_at=datetime.now(timezone.utc),
    ).on_conflict_do_update(
        index_elements=["session_id"],
        set_={"title": title[:200], "updated_at": datetime.now(timezone.utc)},
    )
    await chat_db.execute(stmt)
    await chat_db.commit()
    logger.debug("create_or_update_session_title session_id=%s title=%s", session_id, title[:50])


async def delete_chat(chat_db: AsyncSession, session_id: UUID) -> None:
    """Elimina la sesión y todos sus mensajes."""
    await chat_db.execute(delete(ChatSession).where(ChatSession.session_id == session_id))
    await chat_db.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))
    await chat_db.commit()
    logger.debug("delete_chat session_id=%s", session_id)
