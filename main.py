from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import engine, Base, get_db
import models
import schemas

# Cria o banco e as tabelas automaticamente
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Imunotec Estoque SaaS",
    description="Gerenciador de estoque gratuito para laboratório",
    version="1.0"
)

@app.get("/")
def home():
    return {"status": "API do Imunotec Estoque rodando com sucesso!"}

# Rota para cadastrar um novo lote/reagente
@app.post("/lotes/", response_model=schemas.LoteResponse)
def criar_lote(lote: schemas.LoteCreate, db: Session = Depends(get_db)):
    # Verifica se o número do lote já existe
    db_lote = db.query(models.LoteReagente).filter(models.LoteReagente.numero_lote == lote.numero_lote).first()
    if db_lote:
        raise HTTPException(status_code=400, detail="Este número de lote já está cadastrado.")
    
    novo_lote = models.LoteReagente(**lote.model_dump())
    db.add(novo_lote)
    db.commit()
    db.refresh(novo_lote)
    return novo_lote

# Rota para listar todos os lotes no estoque
@app.get("/lotes/", response_model=List[schemas.LoteResponse])
def listar_lotes(db: Session = Depends(get_db)):
    return db.query(models.LoteReagente).all()

@app.delete("/lotes/{lote_id}")
def eliminar_lote(lote_id: int, db: Session = Depends(get_db)):
    item_lote = db.query(models.LoteReagente).filter(models.LoteReagente.id == lote_id).first()
    
    if not item_lote:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
        
    db.delete(item_lote)
    db.commit()
    return {"mensagem": "Lote eliminado com sucesso"}