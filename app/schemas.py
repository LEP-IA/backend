from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

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

# Token schemas
class Token(BaseModel):
    """Schema para a resposta do token de login."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema para os dados dentro do token JWT."""
    email: Optional[str] = None


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    avatarUrl: Optional[str] = None


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str  # BACKLOG, DOING, DONE
    tag: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    responsibleId: str
    dependencyId: Optional[str] = None


class TaskCreate(BaseModel):
    title: str
    description: str
    status: str = Field(..., pattern="^(BACKLOG|DOING|DONE)$")
    tag: str
    boardId: int
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    responsibleId: str
    dependencyId: Optional[str] = None


class TaskUpdate(BaseModel):
    title: str
    description: str
    status: str = Field(..., pattern="^(BACKLOG|DOING|DONE)$")
    tag: str
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    responsibleId: str
    dependencyId: Optional[str] = None


class TaskDependencySummary(BaseModel):
    id: str
    title: str

class UserSummary(BaseModel):
    id: str
    name: str
    email: EmailStr
    avatarUrl: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: str
    status: str
    tag: str
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    responsible: UserSummary
    dependency: Optional[TaskDependencySummary] = None


class TaskListResponse(BaseModel):
    tasks: List[TaskOut]

class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    termsAccepted: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    user: UserOut


class LogoutRequest(BaseModel):
    pass

class GeneRequest(BaseModel):
    titulo: str
    descricao: str

class GeneResponse(BaseModel):
    titulo_original: str
    descricao_original: str
    titulo_sugerido: str
    descricao_sugerida: str
    resolucoes: list[str]
    nivel_complexidade: str


class UserListResponse(BaseModel):
    users: List[UserOut]

class BoardMembroBase(BaseModel):
    usuario_email: str
    tag: str

class BoardMembroCreate(BoardMembroBase):
    pass

class BoardMembroOut(BoardMembroBase):
    class Config:
        from_attributes = True

class BoardBase(BaseModel):
    nome: str

class BoardCreate(BoardBase):
    pass

class BoardOut(BoardBase):
    id_board: int
    membros: list[BoardMembroOut] = []
    class Config:
        from_attributes = True

class BoardListResponse(BaseModel):
    boards: List[BoardOut]

class BoardUpdate(BaseModel):
    nome: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class SetDonoRequest(BaseModel):
    board_id: int
    usuario_email: EmailStr
