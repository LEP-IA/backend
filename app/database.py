# Configuração de conexão com o banco de dados

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurada. Defina-a no .env para um banco PostgreSQL.")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # evita conexões mortas
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependência do FastAPI para gerenciar a sessão do banco.

    Abre uma sessão por requisição e garante o fechamento ao final.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
