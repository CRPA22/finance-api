"""
Conexión a PostgreSQL con asyncpg (async).

- engine: motor asíncrono
- AsyncSessionLocal: fábrica de sesiones async
- get_db: generador async para FastAPI Depends()
- init_db: crea tablas si no existen (sin datos de prueba)
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

Base = declarative_base()

# postgresql+asyncpg:// para usar el driver asyncpg
engine = create_async_engine(
    settings.database_url,
)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    """
    Generador async: devuelve una sesión, la cierra al terminar.
    """
    async with AsyncSessionLocal() as session:
        yield session


# BD de chat (segunda BD, Docker)
BaseChat = declarative_base()
chat_engine = create_async_engine(settings.chat_database_url)
ChatSessionLocal = async_sessionmaker(
    chat_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_chat_db():
    """Sesión para la BD de historial de chat."""
    async with ChatSessionLocal() as session:
        yield session

