import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Usa PostgreSQL em produção se a variável de ambiente estiver disponível;
# caso contrário, cai para SQLite local para facilitar o desenvolvimento.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    URL_BANCO = DATABASE_URL
    engine_kwargs = {"pool_pre_ping": True}
else:
    URL_BANCO = "sqlite:///./imunotec.db"
    engine_kwargs = {"connect_args": {"check_same_thread": False}}

engine = create_engine(URL_BANCO, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()