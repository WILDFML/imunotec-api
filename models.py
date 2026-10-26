from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from database import AuthBase, StockBase


class LoteReagente(StockBase):
    __tablename__ = "lotes_reagentes"

    id = Column(Integer, primary_key=True, index=True)
    nome_reagente = Column(String(150), nullable=False)
    numero_lote = Column(String(50), unique=True, nullable=False)
    fabricante = Column(String(100))
    quantidade_atual = Column(Float, nullable=False)
    unidade_medida = Column(String(20), nullable=False) # ex: mL, g, unidades
    data_validade = Column(Date, nullable=False)
    temperatura_armazenamento = Column(String(50)) # ex: 2°C a 8°C, -20°C


class Procedimento(StockBase):
    __tablename__ = "procedimentos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False, index=True)
    categoria = Column(String(80), nullable=False, index=True)
    objetivo = Column(Text, nullable=False, default="")
    materiais = Column(Text, nullable=False, default="")
    passos = Column(Text, nullable=False)
    seguranca = Column(Text, nullable=False, default="")
    criado_por = Column(String(150), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    revisado_em = Column(DateTime, default=datetime.utcnow, nullable=False)


class User(AuthBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)


class PasswordResetToken(AuthBase):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)