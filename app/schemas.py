from datetime import datetime
from typing import Annotated, Literal, Optional, List
from pydantic import BaseModel, EmailStr, Field, StringConstraints

TaskStatus = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

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
    status: TaskStatus
    tag: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    responsibleId: str
    dependencyId: Optional[str] = None
    technologies: Optional[List[str]] = None
    complexity: Optional[str] = None
    resolucoes: Optional[List[str]] = None


class TaskCreate(BaseModel):
    title: str
    description: str
    status: TaskStatus
    tag: str
    boardId: int
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    responsibleId: str
    dependencyId: Optional[str] = None
    prioridade: Optional[str] = Field(None, pattern="^(baixo|médio|alto)$")
    technologies: Optional[List[str]] = None
    complexity: Optional[str] = None
    resolucoes: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    title: str
    description: str
    status: TaskStatus
    tag: str
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    responsibleId: str
    dependencyId: Optional[str] = None
    prioridade: Optional[str] = Field(None, pattern="^(baixo|médio|alto)$")
    technologies: Optional[List[str]] = None
    complexity: Optional[str] = None
    resolucoes: Optional[List[str]] = None


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
    prioridade: Optional[str] = None
    technologies: Optional[List[str]] = None
    complexity: Optional[str] = None
    resolucoes: Optional[List[str]] = None
    # Previsão do prazo_model em dias úteis (None se ainda não foi calculada)
    predictedDays: Optional[float] = None
    predictedEffortHours: Optional[float] = None
    # Dias que a tarefa levou: conta ao sair do backlog e congela ao concluir
    daysTaken: int = 0
    # Momentos reais (UTC) de criação e de conclusão; usados no burndown das métricas
    createdAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None


class TaskListResponse(BaseModel):
    tasks: List[TaskOut]


class TaskCommentCreate(BaseModel):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class TaskCommentOut(BaseModel):
    id: str
    text: str
    createdAt: datetime
    author: UserSummary


class TaskCommentListResponse(BaseModel):
    comments: List[TaskCommentOut]

class TaskColumnTimeOut(BaseModel):
    task_id: str
    current_status: str
    # Dias que a tarefa ficou em cada coluna: {"BACKLOG": 2, "DOING": 3}
    days_by_status: dict[str, int]
    # Duração da tarefa: conta ao sair do backlog e congela ao chegar em concluído
    total_days: int

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

class SprintStart(BaseModel):
    duracao_dias: Literal[7, 14]
    # Opcional: início da sprint (ex.: meia-noite local do dono). Padrão: agora.
    inicio: Optional[datetime] = None

class SprintOut(BaseModel):
    ativa: bool = False
    duracao_dias: Optional[int] = None
    inicio: Optional[datetime] = None
    encerrada_em: Optional[datetime] = None
    # Preenchidos só enquanto a sprint está ativa
    numero_atual: Optional[int] = None
    periodo_inicio: Optional[datetime] = None
    periodo_fim: Optional[datetime] = None  # instante em que a sprint atual termina
    # Preenchido só depois de encerrar: quantas sprints o projeto durou
    total_sprints: Optional[int] = None

class BoardOut(BoardBase):
    id_board: int
    membros: list[BoardMembroOut] = []
    sprint: SprintOut = SprintOut()
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

class BoardRepositoryCreate(BaseModel):
    installation_id: int
    repository_id: int

class BoardRepositoryBranchUpdate(BaseModel):
    branch: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    

# ---------------------------------------------------------
# PERFIL PROFISSIONAL GERAL DO USUÁRIO
# ---------------------------------------------------------

class PerfilProfissionalBase(BaseModel):
    area: str
    profession: str
    specialization: str
    role: str
    seniority: str
    experience_time: str


class PerfilProfissionalUpdate(BaseModel):
    area: str
    profession: str
    specialization: str
    role: str
    seniority: str
    experience_time: str


class PerfilProfissionalOut(BaseModel):
    area: Optional[str] = None
    profession: Optional[str] = None
    specialization: Optional[str] = None
    role: Optional[str] = None
    seniority: Optional[str] = None
    experience_time: Optional[str] = None

    class Config:
        from_attributes = True


# ---------------------------------------------------------
# PERFIL PROFISSIONAL DO MEMBRO DENTRO DO BOARD
# ---------------------------------------------------------

class BoardMembroPerfilBase(BaseModel):
    project_role: str
    participation_type: str
    weekly_hours: int = Field(ge=0, le=168)


class BoardMembroPerfilUpdate(BaseModel):
    project_role: str
    participation_type: str
    weekly_hours: int = Field(ge=0, le=168)


class BoardMembroPerfilOut(BaseModel):
    project_role: Optional[str] = None
    participation_type: Optional[str] = None
    weekly_hours: Optional[int] = Field(None, ge=0, le=168)

    class Config:
        from_attributes = True
