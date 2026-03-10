from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatSummary(BaseModel):
    """Resumen de conversación para la lista del frontend."""
    session_id: UUID
    title: str
    updated_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10_000, description="Mensaje del usuario")
    session_id: UUID | None = None


class ChatResponse(BaseModel):
    response: str
    blocks: list[dict] = []
    session_id: UUID
    title: str | None = None  # Solo presente en el primer mensaje de una conversación