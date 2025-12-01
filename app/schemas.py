from datetime import datetime, date, time
from typing import Optional, List
from pydantic import BaseModel

# Formulário para CRIAR um usuário 
class UsuarioCreate(BaseModel):
    email: str
    nome: str
    senha: str  

# Formulário para LER um usuário (o que o backend devolve)
class Usuario(BaseModel):
    email: str
    nome: str
    class Config:
        from_attributes = True 

# Formulário para LOGIN de usuário 
class UsuarioLogin(BaseModel):
    email: str
    senha: str

# Token schemas
class Token(BaseModel):
    """Schema para a resposta do token de login."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema para os dados dentro do token JWT."""
    email: Optional[str] = None

# Schema de criação de Tarefa (o que o usuário envia)
class TarefaCreate(BaseModel):
    id_board: int
    nome: str
    local: Optional[str] = None
    duracao: Optional[str] = None
    hora_inicio: Optional[str] = None
    hora_fim: Optional[str] = None
    local_de_saida: Optional[str] = None
    transporte: Optional[str] = None
    distancia: Optional[str] = None
    # Adicione outros campos relevantes para tarefa

# Schema de Leitura de Tarefa (o que o backend devolve)
class Tarefa(BaseModel):
    id_tarefa: int
    nome: str
    local: Optional[str] = None
    duracao: Optional[str] = None
    hora_inicio: Optional[str] = None
    hora_fim: Optional[str] = None
    local_de_saida: Optional[str] = None
    transporte: Optional[str] = None
    distancia: Optional[str] = None
    maps_info: Optional[dict] = None
    # Adicione outros campos relevantes para tarefa
    class Config:
        from_attributes = True

# Schema para mostrar um Board com suas tarefas
class BoardResponse(BaseModel):
    id_board: int
    nome: str
    tarefas: List[Tarefa] = []
    class Config:
        from_attributes = True

# Schema para mostrar um usuário com seus boards e tarefas
class UsuarioResponseCompleto(Usuario):
    boards: List[BoardResponse] = []
    class Config:
        from_attributes = True