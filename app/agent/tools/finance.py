"""
Parte 1: Funciones que consultan la BD.
Parte 2: Tools de LangChain que envuelven esas funciones (el LLM elige cuándo llamarlas).
"""
import json
from datetime import date, datetime as dt
from typing import Optional

from langchain_core.tools import StructuredTool
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models
from app.core.logging_config import get_logger

logger = get_logger("tools.finance")


async def get_accounts(db: AsyncSession) -> list[dict]:
    """
    Devuelve todas las cuentas con id, nombre, tipo, moneda y balance.
    """
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


async def get_transactions(
    db: AsyncSession,
    account_id: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    category: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """
    Devuelve transacciones con filtros opcionales.
    """
    q = select(models.Transaction)
    if account_id:
        q = q.where(models.Transaction.account_id == account_id)
    if from_date:
        q = q.where(models.Transaction.date >= from_date)
    if to_date:
        q = q.where(models.Transaction.date <= to_date)
    if category:
        q = q.where(models.Transaction.category == category)
    q = q.order_by(models.Transaction.date.desc()).limit(limit)
    result = await db.execute(q)
    rows = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "account_id": str(t.account_id),
            "amount": float(t.amount),
            "type": t.transaction_type,
            "category": t.category,
            "date": t.date.isoformat(),
            "description": t.description,
        }
        for t in rows
    ]


async def get_expenses_by_category(
    db: AsyncSession,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    """
    Agrupa gastos (type='expense') por categoría y devuelve total por categoría.
    """
    q = (
        select(models.Transaction.category, func.sum(models.Transaction.amount).label("total"))
        .where(models.Transaction.transaction_type == "expense")
        .group_by(models.Transaction.category)
    )
    if from_date:
        q = q.where(models.Transaction.date >= from_date)
    if to_date:
        q = q.where(models.Transaction.date <= to_date)
    result = await db.execute(q)
    rows = result.all()
    return {row.category: float(row.total) for row in rows}


# --- Parte 2: Tools para el agente ---
# Cada tool tiene nombre, descripción y parámetros. El LLM usa la descripción
# para decidir cuándo llamarla y con qué argumentos.


def make_finance_tools(db: AsyncSession) -> list:
    """
    Crea los tools de LangChain que usan la sesión `db`.
    Se llama en cada request desde routes (donde tenemos la sesión).
    """

    async def _get_accounts() -> str:
        logger.debug("tool get_accounts invoked")
        data = await get_accounts(db)
        return json.dumps(data, ensure_ascii=False)

    async def _get_transactions(
        account_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        category: Optional[str] = None,
    ) -> str:
        logger.debug("tool get_transactions invoked")
        fd = dt.strptime(from_date, "%Y-%m-%d").date() if from_date else None
        td = dt.strptime(to_date, "%Y-%m-%d").date() if to_date else None
        data = await get_transactions(db, account_id=account_id, from_date=fd, to_date=td, category=category)
        return json.dumps(data, ensure_ascii=False)

    async def _get_expenses_by_category(
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> str:
        logger.debug("tool get_expenses_by_category invoked")
        fd = dt.strptime(from_date, "%Y-%m-%d").date() if from_date else None
        td = dt.strptime(to_date, "%Y-%m-%d").date() if to_date else None
        data = await get_expenses_by_category(db, from_date=fd, to_date=td)
        return json.dumps(data, ensure_ascii=False)

    return [
        StructuredTool.from_function(
            coroutine=_get_accounts,
            name="get_accounts",
            description="Lista todas las cuentas con nombre, tipo, moneda y balance. Úsala cuando pregunten por cuentas, saldos o balance total.",
        ),
        StructuredTool.from_function(
            coroutine=_get_transactions,
            name="get_transactions",
            description="Lista transacciones. Parámetros opcionales: account_id (UUID), from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), category.",
        ),
        StructuredTool.from_function(
            coroutine=_get_expenses_by_category,
            name="get_expenses_by_category",
            description="Devuelve el total de gastos por categoría. Parámetros opcionales: from_date (YYYY-MM-DD), to_date (YYYY-MM-DD).",
        ),
    ]
