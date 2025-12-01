import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models
from .database import get_db
# Configuração do PassLib para hashing de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Funções de segurança relacionadas a senhas e tokens JWT
def gerar_hash(senha: str) -> str:
    """
    Recebe uma senha em texto puro e devolve o hash seguro dela.
    """
    return pwd_context.hash(senha)
# Verifica se a senha bate com o hash
def verificar_senha(senha: str, senha_hash: str) -> bool:
    """
    Compara a senha digitada com o hash salvo no banco.
    Retorna True se for a mesma senha.
    """
    return pwd_context.verify(senha, senha_hash)
# Configurações do JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ni=q*`986pk~c*,*sK!D]=iE@_Zfbqk9xe3T>p2$A*Zu9Xxuv0") 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/login")
# Cria o token de acesso
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """ Cria o JWT. Recebe um dicionário (payload) e um tempo de expiração. """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Adiciona a data de expiração ao payload
    to_encode.update({"exp": expire, "sub": "access_token"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
# Dependência do FastAPI: Obtém o usuário atual a partir do token
def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> models.Usuario:
    """ 
    Dependência do FastAPI: Verifica o token, decodifica, e retorna o objeto Usuário do DB.
    É usada em todas as rotas protegidas (ex: /eventos/).
    """
    # Exceção padrão para credenciais inválidas
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. Decodifica o token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # O dado que identifica o usuário é o email
        email: str = payload.get("email") 
        if email is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception

    # 2. Busca o usuário no banco de dados
    user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if user is None:
        # Se o token for válido, mas o usuário não existir mais
        raise credentials_exception 
        
    return user