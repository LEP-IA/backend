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
)
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

    github_installations_criadas = relationship(
        "GitHubInstallation", back_populates="created_by_user"
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
