# É aqui que a conexão com o database funciona 

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# o core da conexão 
# create_engine é quem sabe falar com o banco usando a DATABASE_URL
engine = create_engine(DATABASE_URL)

# nossa sessão com com o daatabase 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# nossos modelos em models.py herdaram aqui 
Base = declarative_base()

# app/database.py

def get_db():
    """
    Função de dependência do FastAPI para gerenciar a sessão do banco de dados.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



