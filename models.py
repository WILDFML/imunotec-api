from sqlalchemy import Column, Integer, String, Float, Date
from database import Base

class LoteReagente(Base):
    __tablename__ = "lotes_reagentes"

    id = Column(Integer, primary_key=True, index=True)
    nome_reagente = Column(String(150), nullable=False)
    numero_lote = Column(String(50), unique=True, nullable=False)
    fabricante = Column(String(100))
    quantidade_atual = Column(Float, nullable=False)
    unidade_medida = Column(String(20), nullable=False) # ex: mL, g, unidades
    data_validade = Column(Date, nullable=False)
    temperatura_armazenamento = Column(String(50)) # ex: 2°C a 8°C, -20°C