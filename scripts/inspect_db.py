"""
Inspecciona el esquema de la BD PostgreSQL.
Ejecuta: uv run python scripts/inspect_db.py
"""
import sys
from pathlib import Path

# Añade la raíz del proyecto a sys.path para que "app" sea importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

DATABASE_URL = settings.database_url


async def inspect():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name IN ('accounts', 'transactions')
            ORDER BY table_name, ordinal_position
        """))
        rows = result.fetchall()
        print("=== Esquema actual de la BD ===\n")
        current_table = None
        for table, col, dtype, nullable in rows:
            if table != current_table:
                print(f"\n--- {table} ---")
                current_table = table
            print(f"  {col}: {dtype} (nullable={nullable})")
        if not rows:
            print("No se encontraron tablas 'accounts' o 'transactions'.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(inspect())
