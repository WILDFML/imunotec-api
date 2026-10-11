import logging
import os
from typing import List
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from database import (
    AuthBase,
    StockBase,
    auth_engine,
    get_auth_db,
    get_stock_db,
    stock_engine,
)
import models
import schemas

logger = logging.getLogger(__name__)

# Configurações de Segurança (JWT e Hashing)
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("A variável de ambiente SECRET_KEY precisa ser configurada.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Cria as tabelas em cada banco e falha na inicialização se uma conexão não funcionar.
AuthBase.metadata.create_all(bind=auth_engine)
logger.info("Conexão com o banco de autenticação estabelecida.")
StockBase.metadata.create_all(bind=stock_engine)
logger.info("Conexão com o banco de estoque estabelecida.")

app = FastAPI(
    title="Imunotec Estoque SaaS",
    description="Gerenciador de estoque gratuito para laboratório",
    version="1.0"
)

# --- FUNÇÕES AUXILIARES DE SEGURANÇA ---
def verificar_senha(senha_pura, senha_hash):
    return pwd_context.verify(senha_pura, senha_hash)

def obter_hash_senha(senha):
    return pwd_context.hash(senha)

def obter_utilizador_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_auth_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@app.get("/")
def home():
    return {"status": "API do Imunotec Estoque rodando com sucesso!"}

# --- ROTAS DE AUTENTICAÇÃO E UTILIZADORES ---

@app.post("/token", response_model=schemas.Token)
def login_para_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_auth_db),
):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verificar_senha(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou palavra-passe incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user.email, "exp": datetime.utcnow() + access_token_expires}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"access_token": encoded_jwt, "token_type": "bearer"}


# --- ROTAS DE LOTES E REAGENTES (CRUD) ---

@app.post("/lotes/", response_model=schemas.LoteResponse)
def criar_lote(
    lote: schemas.LoteCreate,
    db: Session = Depends(get_stock_db),
    current_user: models.User = Depends(obter_utilizador_atual),
):
    db_lote = db.query(models.LoteReagente).filter(models.LoteReagente.numero_lote == lote.numero_lote).first()
    if db_lote:
        raise HTTPException(status_code=400, detail="Este número de lote já está cadastrado.")
    
    novo_lote = models.LoteReagente(**lote.model_dump())
    db.add(novo_lote)
    db.commit()
    db.refresh(novo_lote)
    return novo_lote

@app.get("/lotes/", response_model=List[schemas.LoteResponse])
def listar_lotes(
    db: Session = Depends(get_stock_db),
    current_user: models.User = Depends(obter_utilizador_atual),
):
    return db.query(models.LoteReagente).all()

@app.delete("/lotes/{lote_id}")
def eliminar_lote(
    lote_id: int,
    db: Session = Depends(get_stock_db),
    current_user: models.User = Depends(obter_utilizador_atual),
):
    item_lote = db.query(models.LoteReagente).filter(models.LoteReagente.id == lote_id).first()
    
    if not item_lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
        
    db.delete(item_lote)
    db.commit()
    return {"mensagem": "Lote eliminado com sucesso"}

@app.patch("/lotes/{lote_id}/adicionar")
def adicionar_quantidade(
    lote_id: int,
    quantidade_extra: float,
    db: Session = Depends(get_stock_db),
    current_user: models.User = Depends(obter_utilizador_atual),
):
    item_lote = db.query(models.LoteReagente).filter(models.LoteReagente.id == lote_id).first()
    
    if not item_lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
        
    item_lote.quantidade_atual += quantidade_extra
    db.commit()
    db.refresh(item_lote)
    return {"mensagem": "Quantidade atualizada com sucesso", "nova_quantidade": item_lote.quantidade_atual}