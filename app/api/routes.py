import time
import uuid

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatRequest, ChatResponse, ChatSummary
from app.agent.agent import get_response_with_tools, parse_chat_response, generate_chat_title
from app.agent.tools.finance import make_finance_tools
from app.db.database import get_db, get_chat_db
from app.db.chat_history import get_chat_history, save_message, list_chats, create_or_update_session_title, delete_chat
from app.db import models
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger("routes")


@router.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running"}


@router.get("/chats", response_model=list[ChatSummary])
async def list_conversations(
    chat_db: AsyncSession = Depends(get_chat_db),
) -> list[ChatSummary]:
    """Lista todas las conversaciones con título y fecha. Ordenadas por última actualización."""
    rows = await list_chats(chat_db)
    return [ChatSummary(**r) for r in rows]


@router.get("/chat/history")
async def get_conversation_history(
    session_id: uuid.UUID,
    chat_db: AsyncSession = Depends(get_chat_db),
):
    """Devuelve los mensajes de una conversación."""
    history = await get_chat_history(chat_db, session_id, limit=200)
    if not history:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return [{"role": r.role, "content": r.content} for r in history]


@router.delete("/chat/{session_id}", status_code=204)
async def delete_conversation(
    session_id: uuid.UUID,
    chat_db: AsyncSession = Depends(get_chat_db),
) -> None:
    """Elimina una conversación y todos sus mensajes."""
    await delete_chat(chat_db, session_id)


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    chat_db: AsyncSession = Depends(get_chat_db),
) -> ChatResponse:
    session_id = request.session_id or uuid.uuid4()
    start = time.perf_counter()
    try:
        logger.info("chat request session_id=%s", session_id)

        history_rows = await get_chat_history(chat_db, session_id)
        history = [(r.role, r.content) for r in history_rows]

        tools = make_finance_tools(db)
        raw_response, total_tokens = await get_response_with_tools(
            request.message, tools, history=history
        )
        response_text, blocks = parse_chat_response(raw_response)

        await save_message(chat_db, session_id, "user", request.message)
        await save_message(chat_db, session_id, "assistant", response_text)

        # Generar y guardar título si es el primer intercambio de la sesión
        title = None
        if len(history_rows) == 0:
            try:
                title = await generate_chat_title(request.message)
                await create_or_update_session_title(chat_db, session_id, title)
            except Exception as title_err:
                logger.warning("generate_chat_title failed session_id=%s: %s", session_id, title_err)
                title = "Nueva conversación"
                await create_or_update_session_title(chat_db, session_id, title)

        duration = time.perf_counter() - start
        logger.info(
            "chat completed session_id=%s total_tokens=%s duration=%.2fs",
            session_id, total_tokens, duration,
        )

        return ChatResponse(
            response=response_text, blocks=blocks, session_id=session_id, title=title
        )
    except Exception as e:
        logger.error("chat failed session_id=%s error=%s", session_id, str(e))
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    """Lista todas las cuentas."""
    result = await db.execute(select(models.Account))
    accounts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "type": a.account_type,
            "currency": a.currency,
            "balance": float(a.balance),
        }
        for a in accounts
    ]