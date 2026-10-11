import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")
STOCK_DATABASE_URL = os.getenv("STOCK_DATABASE_URL")

if DATABASE_URL and not STOCK_DATABASE_URL:
    raise RuntimeError(
        "A variável de ambiente STOCK_DATABASE_URL precisa ser configurada "
        "quando DATABASE_URL estiver definida."
    )

LOCAL_DATABASE_URL = "sqlite:///./imunotec.db"
auth_database_url = DATABASE_URL or LOCAL_DATABASE_URL
stock_database_url = STOCK_DATABASE_URL or LOCAL_DATABASE_URL


def _create_engine(database_url: str):
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url, connect_args={"check_same_thread": False}
        )
    if database_url.startswith("postgres://"):
        database_url = (
            "postgresql+psycopg://" + database_url[len("postgres://"):]
        )
    elif database_url.startswith("postgresql://"):
        database_url = (
            "postgresql+psycopg://" + database_url[len("postgresql://"):]
        )
    return create_engine(database_url, pool_pre_ping=True)


auth_engine = _create_engine(auth_database_url)
stock_engine = _create_engine(stock_database_url)

AuthBase = declarative_base()
StockBase = declarative_base()

AuthSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=auth_engine
)
StockSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=stock_engine
)


def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_stock_db():
    db = StockSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db():
    yield from get_auth_db()
