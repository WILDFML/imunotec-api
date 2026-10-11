from sqlalchemy import Column, Integer, String, Float, Date, Boolean
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

class User(AuthBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)