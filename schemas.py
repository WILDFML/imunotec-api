from datetime import date
from pydantic import BaseModel

class LoteCreate(BaseModel):
    nome_reagente: str
    numero_lote: str
    fabricante: str
    quantidade_atual: float
    unidade_medida: str  # ex: mL, g, frascos
    data_validade: date
    temperatura_armazenamento: str  # ex: 2°C a 8°C

class LoteResponse(LoteCreate):
    id: int

    class Config:
        from_attributes = True