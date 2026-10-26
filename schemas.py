from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

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


class ProcedimentoCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    categoria: str = Field(min_length=1, max_length=80)
    objetivo: str = Field(default="", max_length=10000)
    materiais: str = Field(default="", max_length=10000)
    passos: str = Field(min_length=1, max_length=30000)
    seguranca: str = Field(default="", max_length=10000)

    @field_validator(
        "titulo", "categoria", "objetivo", "materiais", "passos", "seguranca"
    )
    @classmethod
    def remover_espacos_externos(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("titulo", "categoria", "passos")
    @classmethod
    def rejeitar_valor_vazio(cls, valor: str) -> str:
        if not valor:
            raise ValueError("Este campo não pode ficar vazio.")
        return valor


class ProcedimentoResponse(ProcedimentoCreate):
    id: int
    criado_por: str
    criado_em: datetime
    atualizado_em: datetime
    revisado_em: datetime

    class Config:
        from_attributes = True


# --- NOVOS SCHEMAS PARA UTILIZADORES E AUTH ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    id: int
    email: str
    ativo: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None