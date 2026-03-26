from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base

# Tabelas Presentes no database 
class Usuario(Base):
    __tablename__ = "usuario"

    email = Column(String, primary_key=True, index=True)
    nome = Column(String)
    senha_hash = Column(Text)
    avatar_url = Column(String, nullable=True)  # URL opcional do avatar do usuário

    # Relacionamentos 
    chats = relationship("ChatIA", back_populates="usuario")
    boards = relationship("Board", back_populates="usuario")

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
    usuario_email = Column(String, ForeignKey("usuario.email"), nullable=False) # não pode ficar vazio

    # Relacionamentos
    usuario = relationship("Usuario", back_populates="boards")

    # Um calendário tem muitos 'eventos'
    # O back_populates aponta para a propriedade 'calendario' no modelo Evento
    tarefas = relationship("Tarefa", back_populates="board", cascade="all, delete-orphan")

class Tarefa(Base):
    __tablename__ = "tarefa"

    id_tarefa = Column(Integer, primary_key=True, index=True)

    # Chaves estrangeiras
    id_board = Column(Integer, ForeignKey("board.id_board"), nullable=False)
    responsavel_email = Column(String, ForeignKey("usuario.email"), nullable=False)
    dependencia_id = Column(Integer, ForeignKey("tarefa.id_tarefa", ondelete="SET NULL"), nullable=True)

    # Campos principais da tarefa no padrão do README
    titulo = Column(String, nullable=False)
    descricao = Column(Text, nullable=True)
    status = Column(String, nullable=False, index=True)  # BACKLOG, DOING, DONE
    tag = Column(String, nullable=True)  # ex: #FRONTEND, #BACKEND

    # Datas de início e fim em formato datetime
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)

    # Relacionamentos
    board = relationship("Board", back_populates="tarefas")
    responsavel = relationship("Usuario")
    dependencia = relationship("Tarefa", remote_side=[id_tarefa], uselist=False)
