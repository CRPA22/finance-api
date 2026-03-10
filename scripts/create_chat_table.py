"""
Crea la tabla chat_messages en la BD de chat.
Ejecutar: uv run python scripts/create_chat_table.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.db.database import BaseChat
from app.db.chat_models import ChatMessage, ChatSession  # noqa: F401 - registra los modelos


async def main():
    engine = create_async_engine(settings.chat_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(BaseChat.metadata.create_all)
    print("Tablas chat_messages y chat_sessions creadas.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
