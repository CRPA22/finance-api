"""
Modelos adaptados al esquema real de PostgreSQL.

Cuando el nombre de columna en la BD difiere del atributo en Python,
usamos el primer argumento de Column("nombre_en_bd", tipo).
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(100), nullable=False)
    account_type = Column("type", String(20), nullable=False)  # columna BD = "type"
    currency = Column(String(3), nullable=False)
    balance = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Account {self.name} ({self.balance})>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column("type", String(20), nullable=False)  # income o expense
    category = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.transaction_type} {self.amount} ({self.category})>"
