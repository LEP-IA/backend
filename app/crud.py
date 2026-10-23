from datetime import datetime, timezone
from sqlalchemy.orm import Session, selectinload
from . import models, schemas
from .services import prazo_service, task_time_service


def get_task_by_id(db: Session, task_id: int) -> models.Tarefa | None:
    return db.query(models.Tarefa).filter(models.Tarefa.id_tarefa == task_id).first()

def list_tasks(db: Session) -> list[models.Tarefa]:
    """Retorna todas as tarefas idependente do board board."""
    return (
        db.query(models.Tarefa)
        .options(selectinload(models.Tarefa.historico_colunas))
        .all()
    )

def list_tasks_by_board(db: Session, board_id: int) -> list[models.Tarefa]:
    """Retorna todas as tarefas filtradas pelo ID do board."""
    return (
        db.query(models.Tarefa)
        .options(selectinload(models.Tarefa.historico_colunas))
        .filter(models.Tarefa.id_board == board_id)
        .all()
    )

def get_board(db: Session, board_id: int):
    return db.query(models.Board).filter(models.Board.id_board == board_id).first()


def create_task(db: Session, task_in: schemas.TaskCreate) -> models.Tarefa:
    # Busca responsável
    responsavel = db.query(models.Usuario).filter(models.Usuario.email == task_in.responsibleId).first()
    if not responsavel:
        raise ValueError("Responsável não encontrado")

    # Verifica se o board existe
    board = db.query(models.Board).filter(models.Board.id_board == task_in.boardId).first()
    if not board:
        raise ValueError("Board não encontrado")

    dependencia = None
    if task_in.dependencyId:
        dependencia = db.query(models.Tarefa).filter(models.Tarefa.id_tarefa == int(task_in.dependencyId)).first()

    db_task = models.Tarefa(
        id_board=task_in.boardId,
        responsavel_email=responsavel.email,
        titulo=task_in.title,
        descricao=task_in.description,
        status=task_in.status,
        tag=task_in.tag,
        data_inicio=task_in.startDate,
        data_fim=None,  # calculada pela previsão (início + prazo previsto)
        dependencia_id=dependencia.id_tarefa if dependencia else None,
        prioridade=task_in.prioridade,
        technologies=task_in.technologies,
        complexity=task_in.complexity,
    )
    db.add(db_task)
    # Começa a contar o tempo da tarefa na coluna em que ela foi criada
    task_time_service.registrar_mudanca_status(db, db_task, db_task.status)
    db.commit()
    db.refresh(db_task)

    # A previsão precisa do id da tarefa, por isso só é pedida depois de salvar
    _atualizar_previsao(db, db_task)
    return db_task


def _atualizar_previsao(db: Session, task_db: models.Tarefa) -> bool:
    """Pede a previsão ao prazo_model e salva. Falhas não afetam a tarefa."""
    if prazo_service.atualizar_previsao(db, task_db):
        db.commit()
        db.refresh(task_db)
        return True
    return False


def update_task(db: Session, task_id: int, task_in: schemas.TaskUpdate) -> models.Tarefa | None:
    task_db = get_task_by_id(db, task_id)
    if not task_db:
        return None

    responsavel = db.query(models.Usuario).filter(models.Usuario.email == task_in.responsibleId).first()
    if not responsavel:
        raise ValueError("Responsável não encontrado")

    dependencia = None
    if task_in.dependencyId:
        dependencia = db.query(models.Tarefa).filter(models.Tarefa.id_tarefa == int(task_in.dependencyId)).first()

    # Dados que alimentam o prazo_model: se mudarem, a previsão é refeita
    entrada_anterior = (
        task_db.responsavel_email,
        task_db.complexity,
        task_db.prioridade,
    )
    inicio_anterior = task_db.data_inicio

    task_db.titulo = task_in.title
    task_db.descricao = task_in.description
    # Se mudou de coluna, fecha a passagem anterior e abre a da nova coluna
    task_time_service.registrar_mudanca_status(db, task_db, task_in.status)
    task_db.status = task_in.status
    task_db.tag = task_in.tag
    # A data de início é informada; a de fim é sempre calculada pela previsão
    # (endDate enviado pelo cliente é ignorado). Sem startDate na requisição,
    # mantém a data salva.
    if "startDate" in task_in.model_fields_set:
        task_db.data_inicio = task_in.startDate
    task_db.responsavel_email = responsavel.email
    task_db.dependencia_id = dependencia.id_tarefa if dependencia else None
    task_db.prioridade = task_in.prioridade
    task_db.technologies = task_in.technologies
    task_db.complexity = task_in.complexity

    db.commit()
    db.refresh(task_db)

    entrada_atual = (
        task_db.responsavel_email,
        task_db.complexity,
        task_db.prioridade,
    )
    # Também tenta de novo quando a tarefa ainda não tem previsão
    atualizou = False
    if entrada_atual != entrada_anterior or task_db.previsao_dias is None:
        atualizou = _atualizar_previsao(db, task_db)

    # Mudou só o início: a previsão vale, então só move a data de fim
    if (
        not atualizou
        and task_db.data_inicio != inicio_anterior
        and prazo_service.recalcular_datas(task_db)
    ):
        db.commit()
        db.refresh(task_db)
    return task_db


def delete_task(db: Session, task_id: int) -> bool:
    task_db = get_task_by_id(db, task_id)
    if not task_db:
        return False
    db.delete(task_db)
    db.commit()
    return True


# Helper para converter model em resposta do contrato

def build_task_out(task: models.Tarefa) -> schemas.TaskOut:
    responsible = schemas.UserSummary(
        id=str(task.responsavel.email),
        name=task.responsavel.nome,
        email=task.responsavel.email,
        avatarUrl=None,
    )
    dependency = None
    if task.dependencia:
        dependency = schemas.TaskDependencySummary(
            id=str(task.dependencia.id_tarefa),
            title=task.dependencia.titulo,
        )

    return schemas.TaskOut(
        id=str(task.id_tarefa),
        title=task.titulo,
        description=task.descricao,
        status=task.status,
        tag=task.tag,
        startDate=task.data_inicio,
        endDate=task.data_fim,
        responsible=responsible,
        dependency=dependency,
        prioridade=task.prioridade,
        technologies=task.technologies,
        complexity=task.complexity,
        predictedDays=task.previsao_dias,
        predictedEffortHours=task.previsao_esforco_horas,
        daysTaken=task_time_service.dias_de_duracao(task),
        createdAt=task_time_service.criada_em(task),
        completedAt=task_time_service.concluida_em(task),
    )

def build_user_out(user: models.Usuario) -> schemas.UserOut:
    return schemas.UserOut(
        id=user.email,       # No seu banco, o email é a chave primária
        name=user.nome,      # Mapeia 'nome' para 'name'
        email=user.email,
        avatarUrl=user.avatar_url
    )

def list_users(db: Session) -> list[models.Usuario]:
    """Retorna todos os usuários cadastrados."""
    return db.query(models.Usuario).all()

# Adicione ao final do seu crud.py
def build_user_out(user: models.Usuario) -> schemas.UserOut:
    """Converte o modelo do banco para o schema UserOut do frontend."""
    return schemas.UserOut(
        id=user.email,       # Usando email como ID conforme seu banco
        name=user.nome,      # Traduzindo 'nome' para 'name'
        email=user.email,
        avatarUrl=user.avatar_url if hasattr(user, 'avatar_url') else None
    )

def get_user_by_email(db: Session, email: str):
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()

def is_user_board_member(db: Session, board_id: int, usuario_email: str) -> bool:
    return db.query(models.BoardMembro).filter(
        models.BoardMembro.board_id == board_id,
        models.BoardMembro.usuario_email == usuario_email
    ).first() is not None

def list_task_comments(db: Session, task_id: int) -> list[models.TarefaComentario]:
    return (
        db.query(models.TarefaComentario)
        .options(selectinload(models.TarefaComentario.autor))
        .filter(models.TarefaComentario.tarefa_id == task_id)
        .order_by(models.TarefaComentario.criado_em.asc())
        .all()
    )


def create_task_comment(
    db: Session, task_id: int, autor_email: str, texto: str
) -> models.TarefaComentario | None:
    if get_task_by_id(db, task_id) is None:
        return None

    comment = models.TarefaComentario(
        tarefa_id=task_id,
        autor_email=autor_email,
        texto=texto,
        criado_em=datetime.now(timezone.utc),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return (
        db.query(models.TarefaComentario)
        .options(selectinload(models.TarefaComentario.autor))
        .filter(models.TarefaComentario.id == comment.id)
        .one()
    )


def build_comment_out(comment: models.TarefaComentario) -> schemas.TaskCommentOut:
    autor = comment.autor
    return schemas.TaskCommentOut(
        id=str(comment.id),
        text=comment.texto,
        createdAt=comment.criado_em,
        author=schemas.UserSummary(
            id=autor.email,
            name=autor.nome or autor.email,
            email=autor.email,
            avatarUrl=autor.avatar_url,
        ),
    )


def add_board_member(db: Session, board_id: int, usuario_email: str, tag: str):
    membro = models.BoardMembro(board_id=board_id, usuario_email=usuario_email, tag=tag)
    db.add(membro)
    db.commit()
    db.refresh(membro)
    return membro
