from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

# Tabelas Presentes no database 
class Usuario(Base):
    __tablename__ = "usuario"

    email = Column(String, primary_key=True, index=True)
    nome = Column(String)
    senha_hash = Column(Text)

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
    tarefas = relationship("Tarefa", back_populates="board")

class Tarefa(Base):
    __tablename__ = "tarefa"

    id_tarefa = Column(Integer, primary_key=True, index=True)

    # Chave estrangeira
    id_board = Column(Integer, ForeignKey("board.id_board"), nullable=False)

    nome = Column(String)
    local = Column(String) #local do evento
    duracao = Column(String)
    hora_inicio = Column(String)
    hora_fim = Column(String)
    local_de_saida = Column(String) #local de onde o usuario vai sair
    transporte = Column(String)
    distancia = Column(String)


    # O back_populates aponta para a propriedade 'eventos' (plural) no modelo Calendario
    board = relationship("Board", back_populates="tarefas")
