from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from .database import Base


class Usuario(Base):
    __tablename__ = "usuario"

    email = Column(String, primary_key=True, index=True)
    nome = Column(String)
    senha_hash = Column(Text)
    avatar_url = Column(String, nullable=True)  # URL opcional do avatar do usuário

    # Relacionamentos
    chats = relationship("ChatIA", back_populates="usuario")
    boards = relationship("Board", back_populates="usuario")
    membro_boards = relationship(
        "BoardMembro", back_populates="usuario", cascade="all, delete-orphan"
    )

    # Perfil profissional geral do usuário
    perfil_profissional = relationship(
        "PerfilProfissional",
        back_populates="usuario",
        uselist=False,
        cascade="all, delete-orphan",
    )

    github_installations_criadas = relationship(
        "GitHubInstallation", back_populates="created_by_user"
    )


class PerfilProfissional(Base):
    __tablename__ = "perfil_profissional"

    # 1 usuário possui no máximo 1 perfil profissional.
    # Por isso usuario_email também é a chave primária.
    usuario_email = Column(
        String,
        ForeignKey("usuario.email", ondelete="CASCADE"),
        primary_key=True,
    )

    # Dados gerais do questionário profissional
    area = Column(String, nullable=True)
    profession = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    role = Column(String, nullable=True)
    seniority = Column(String, nullable=True)
    experience_time = Column(String, nullable=True)

    # Relacionamento
    usuario = relationship(
        "Usuario",
        back_populates="perfil_profissional",
    )


class ChatIA(Base):
    __tablename__ = "chatia"

    id_chat = Column(Integer, primary_key=True, index=True)
    pergunta = Column(String)
    resposta = Column(String)

    # Chave estrangeira
    usuario_email = Column(String, ForeignKey("usuario.email"), nullable=False)

    # Relacionamento
    usuario = relationship("Usuario", back_populates="chats")


class Board(Base):
    __tablename__ = "board"

    id_board = Column(Integer, primary_key=True, index=True)
    nome = Column(String)

    # Sprints do board.
    # Sprint ativa: sprint_inicio preenchido e sprint_encerrada_em vazio.
    # O número da sprint atual é calculado a partir de sprint_inicio e
    # sprint_duracao_dias, então não precisa ser salvo.
    sprint_duracao_dias = Column(Integer, nullable=True)  # 7 ou 14
    sprint_inicio = Column(DateTime(timezone=True), nullable=True)
    sprint_encerrada_em = Column(DateTime(timezone=True), nullable=True)
    sprint_total = Column(Integer, nullable=True)  # sprints que durou ao encerrar

    __table_args__ = (
        CheckConstraint(
            "sprint_duracao_dias IS NULL OR sprint_duracao_dias IN (7, 14)",
            name="ck_board_sprint_duracao_dias",
        ),
    )

    # Chave estrangeira
    usuario_email = Column(
        String, ForeignKey("usuario.email"), nullable=False
    )  # não pode ficar vazio

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="boards")
    membros = relationship(
        "BoardMembro", back_populates="board", cascade="all, delete-orphan"
    )

    # O back_populates aponta para a propriedade 'calendario' no modelo Evento
    tarefas = relationship(
        "Tarefa", back_populates="board", cascade="all, delete-orphan"
    )

    repositories = relationship(
        "BoardRepository",
        back_populates="board",
        cascade="all, delete-orphan",
    )


class Tarefa(Base):
    __tablename__ = "tarefa"

    id_tarefa = Column(Integer, primary_key=True, index=True)

    # Chaves estrangeiras
    id_board = Column(Integer, ForeignKey("board.id_board"), nullable=False)
    responsavel_email = Column(String, ForeignKey("usuario.email"), nullable=False)
    dependencia_id = Column(
        Integer, ForeignKey("tarefa.id_tarefa", ondelete="SET NULL"), nullable=True
    )

    # Campos principais da tarefa no padrão do README
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    status = Column(String, nullable=False, index=True)  # BACKLOG, DOING, DONE
    tag = Column(String, nullable=True)  # ex: #FRONTEND, #BACKEND
    prioridade = Column(String, nullable=True)  # baixo, médio, alto
    technologies = Column(ARRAY(String), nullable=True)
    complexity = Column(String, nullable=True)

    # Datas de início e fim em formato datetime
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)

    # Relacionamentos
    board = relationship("Board", back_populates="tarefas")
    responsavel = relationship("Usuario")
    dependencia = relationship("Tarefa", remote_side=[id_tarefa], uselist=False)


class BoardMembro(Base):
    __tablename__ = "board_membro"

    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("board.id_board"), nullable=False)
    usuario_email = Column(String, ForeignKey("usuario.email"), nullable=False)
    tag = Column(String)

    project_role = Column(String, nullable=True)
    participation_type = Column(String, nullable=True)
    weekly_hours = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "board_id",
            "usuario_email",
            name="uq_board_membro",
        ),
        CheckConstraint(
            "weekly_hours IS NULL OR " 
            "(weekly_hours >= 0 AND weekly_hours <= 168)",
            name="ck_board_membro_weekly_hours",
        ),
    )

    board = relationship("Board", back_populates="membros")
    usuario = relationship("Usuario", back_populates="membro_boards")


class GitHubInstallation(Base):
    __tablename__ = "github_installation"

    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(BigInteger, unique=True, nullable=False, index=True)
    account_id = Column(BigInteger, nullable=False, index=True)
    account_login = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    repository_selection = Column(String, nullable=True)
    created_by_email = Column(
        String, ForeignKey("usuario.email", ondelete="SET NULL"), nullable=True
    )
    created_by_user = relationship(
        "Usuario", back_populates="github_installations_criadas"
    )

    board_repositories = relationship(
        "BoardRepository",
        back_populates="github_installation",
        cascade="all, delete-orphan",
    )


class BoardRepository(Base):
    __tablename__ = "board_repository"

    id = Column(Integer, primary_key=True, index=True)

    board_id = Column(
        Integer, ForeignKey("board.id_board", ondelete="CASCADE"), nullable=False
    )

    github_installation_id = Column(
        Integer,
        ForeignKey("github_installation.id", ondelete="CASCADE"),
        nullable=False,
    )

    repository_id = Column(BigInteger, nullable=False)

    repository_name = Column(String, nullable=False)

    repository_full_name = Column(String, nullable=False)

    default_branch = Column(String, nullable=False)

    private = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint("board_id", "repository_id", name="uq_board_repository"),
    )

    board = relationship(
        "Board",
        back_populates="repositories",
    )

    github_installation = relationship(
        "GitHubInstallation",
        back_populates="board_repositories",
    )
