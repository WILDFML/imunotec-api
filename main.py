import hashlib
import hmac
import logging
import os
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import List, TypedDict
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import FastAPI, Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
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
ACCOUNT_CREATION_KEY = os.getenv("ACCOUNT_CREATION_KEY")
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class ConfiguracaoEmail(TypedDict):
    host: str
    port: int
    username: str
    password: str
    from_email: str
    frontend_url: str


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


def configuracao_email() -> ConfiguracaoEmail:
    host = os.getenv("SMTP_HOST")
    porta = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    frontend_url = os.getenv("FRONTEND_URL")
    if (
        not host
        or not porta
        or not username
        or not password
        or not from_email
        or not frontend_url
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="O serviço de recuperação de senha não está configurado.",
        )

    try:
        porta_int = int(porta)
    except ValueError as erro:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A porta SMTP configurada é inválida.",
        ) from erro

    url_frontend = urlsplit(frontend_url)
    if url_frontend.scheme not in ("http", "https") or not url_frontend.netloc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A URL do aplicativo para recuperação de senha é inválida.",
        )
    return {
        "host": host,
        "port": porta_int,
        "username": username,
        "password": password,
        "from_email": from_email,
        "frontend_url": frontend_url,
    }


def enviar_email_recuperacao(
    destinatario: str, token: str, configuracao: ConfiguracaoEmail
) -> None:
    partes_url = urlsplit(configuracao["frontend_url"])
    parametros = parse_qsl(partes_url.query, keep_blank_values=True)
    parametros.append(("reset_token", token))
    link_recuperacao = urlunsplit(
        (
            partes_url.scheme,
            partes_url.netloc,
            partes_url.path,
            urlencode(parametros),
            "",
        )
    )

    mensagem = EmailMessage()
    mensagem["Subject"] = "Recuperação de senha do Imunotec"
    mensagem["From"] = configuracao["from_email"]
    mensagem["To"] = destinatario
    mensagem.set_content(
        "Recebemos uma solicitação para redefinir a senha da sua conta "
        "Imunotec.\n\n"
        f"Acesse este link para criar uma nova senha (válido por "
        f"{PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutos e utilizável uma "
        f"única vez):\n{link_recuperacao}\n\n"
        "Se você não solicitou esta alteração, ignore este e-mail."
    )

    try:
        if configuracao["port"] == 465:
            with smtplib.SMTP_SSL(
                configuracao["host"], configuracao["port"], timeout=15
            ) as servidor:
                servidor.login(
                    configuracao["username"], configuracao["password"]
                )
                servidor.send_message(mensagem)
        else:
            with smtplib.SMTP(
                configuracao["host"], configuracao["port"], timeout=15
            ) as servidor:
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
                servidor.login(
                    configuracao["username"], configuracao["password"]
                )
                servidor.send_message(mensagem)
    except (OSError, smtplib.SMTPException):
        logger.exception("Falha ao enviar e-mail de recuperação de senha.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível enviar o e-mail de recuperação agora.",
        )


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

@app.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def registar_utilizador(
    user_data: schemas.UserCreate,
    x_registration_key: str | None = Header(default=None),
    db: Session = Depends(get_auth_db),
):
    if not ACCOUNT_CREATION_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A criação de contas não está configurada.",
        )
    if x_registration_key is None or not hmac.compare_digest(
        x_registration_key.encode("utf-8"),
        ACCOUNT_CREATION_KEY.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chave de criação inválida.",
        )

    email = str(user_data.email).strip().lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este e-mail.",
        )

    user = models.User(
        email=email,
        hashed_password=obter_hash_senha(user_data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este e-mail.",
        )
    db.refresh(user)
    return user


@app.post("/token", response_model=schemas.Token)
def login_para_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_auth_db),
):
    email = form_data.username.strip().lower()
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
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


@app.post(
    "/password-reset-request",
    status_code=status.HTTP_202_ACCEPTED,
)
def solicitar_recuperacao_senha(
    pedido: schemas.PasswordResetRequest,
    db: Session = Depends(get_auth_db),
):
    configuracao = configuracao_email()
    email = str(pedido.email).strip().lower()
    user = db.query(models.User).filter(func.lower(models.User.email) == email).first()
    if user is None:
        return {
            "mensagem": (
                "Se o e-mail estiver cadastrado, você receberá instruções "
                "para redefinir a senha."
            )
        }

    agora = datetime.utcnow()
    pedido_recente = (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.user_id == user.id,
            models.PasswordResetToken.created_at
            >= agora - timedelta(minutes=1),
        )
        .first()
    )
    if pedido_recente:
        return {
            "mensagem": (
                "Se o e-mail estiver cadastrado, você receberá instruções "
                "para redefinir a senha."
            )
        }

    token = secrets.token_urlsafe(32)
    db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id
    ).delete(synchronize_session=False)
    db.add(
        models.PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            created_at=agora,
            expires_at=agora
            + timedelta(minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
    )
    enviar_email_recuperacao(user.email, token, configuracao)
    db.commit()

    return {
        "mensagem": (
            "Se o e-mail estiver cadastrado, você receberá instruções "
            "para redefinir a senha."
        )
    }


@app.post("/password-reset-confirm")
def confirmar_recuperacao_senha(
    pedido: schemas.PasswordResetConfirm,
    db: Session = Depends(get_auth_db),
):
    token_hash = hashlib.sha256(pedido.token.encode("utf-8")).hexdigest()
    agora = datetime.utcnow()
    registro = (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.token_hash == token_hash,
            models.PasswordResetToken.expires_at > agora,
        )
        .with_for_update()
        .first()
    )
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O link de recuperação é inválido ou expirou.",
        )

    user = db.query(models.User).filter(models.User.id == registro.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O link de recuperação é inválido ou expirou.",
        )

    token_removido = (
        db.query(models.PasswordResetToken)
        .filter(
            models.PasswordResetToken.id == registro.id,
            models.PasswordResetToken.expires_at > agora,
        )
        .delete(synchronize_session=False)
    )
    if token_removido != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O link de recuperação é inválido ou expirou.",
        )

    user.hashed_password = obter_hash_senha(pedido.password)
    db.commit()
    return {"mensagem": "Senha redefinida com sucesso."}


@app.get("/favoritos/procedimentos", response_model=List[str])
def listar_procedimentos_favoritos(
    db: Session = Depends(get_auth_db),
    current_user: models.User = Depends(obter_utilizador_atual),
):
    favoritos = (
        db.query(models.ProcedimentoFavorito.arquivo)
        .filter(models.ProcedimentoFavorito.user_id == current_user.id)
        .order_by(models.ProcedimentoFavorito.arquivo)
        .all()
    )
    return [arquivo for (arquivo,) in favoritos]


@app.post("/favoritos/procedimentos")
def favoritar_procedimento(
    dados: schemas.ProcedimentoFavoritoCreate,
    db: Session = Depends(get_auth_db),
    current_user: models.User = Depends(obter_utilizador_atual),
):
    favorito_existente = (
        db.query(models.ProcedimentoFavorito)
        .filter(
            models.ProcedimentoFavorito.user_id == current_user.id,
            models.ProcedimentoFavorito.arquivo == dados.arquivo,
        )
        .first()
    )
    if favorito_existente is None:
        db.add(
            models.ProcedimentoFavorito(
                user_id=current_user.id,
                arquivo=dados.arquivo,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            favorito_existente = (
                db.query(models.ProcedimentoFavorito)
                .filter(
                    models.ProcedimentoFavorito.user_id == current_user.id,
                    models.ProcedimentoFavorito.arquivo == dados.arquivo,
                )
                .first()
            )
            if favorito_existente is None:
                raise
    return {"mensagem": "Procedimento adicionado aos favoritos."}


@app.delete("/favoritos/procedimentos")
def desfavoritar_procedimento(
    dados: schemas.ProcedimentoFavoritoCreate,
    db: Session = Depends(get_auth_db),
    current_user: models.User = Depends(obter_utilizador_atual),
):
    (
        db.query(models.ProcedimentoFavorito)
        .filter(
            models.ProcedimentoFavorito.user_id == current_user.id,
            models.ProcedimentoFavorito.arquivo == dados.arquivo,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"mensagem": "Procedimento removido dos favoritos."}


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
