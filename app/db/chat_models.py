"""
Modelo para historial de chat. Usa BaseChat (BD separada).

- ChatMessage: cada mensaje individual (user/assistant).
- ChatSession: metadatos por conversación (título generado por IA, updated_at).
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.database import BaseChat


class ChatSession(BaseChat):
    """
    Una fila por conversación. Guarda el título generado por la IA
    para mostrarlo en la lista izquierda del frontend.
    """
    __tablename__ = "chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String(200), nullable=False, default="Nueva conversación")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ChatMessage(BaseChat):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
