from sqlalchemy.orm import Session
from . import models, schemas


def get_task_by_id(db: Session, task_id: int) -> models.Tarefa | None:
    return db.query(models.Tarefa).filter(models.Tarefa.id_tarefa == task_id).first()


def list_tasks(db: Session) -> list[models.Tarefa]:
    return db.query(models.Tarefa).all()


def create_task(db: Session, task_in: schemas.TaskCreate) -> models.Tarefa:
    # Busca responsável
    responsavel = db.query(models.Usuario).filter(models.Usuario.email == task_in.responsibleId).first()
    if not responsavel:
        raise ValueError("Responsável não encontrado")

    dependencia = None
    if task_in.dependencyId:
        dependencia = db.query(models.Tarefa).filter(models.Tarefa.id_tarefa == int(task_in.dependencyId)).first()

    db_task = models.Tarefa(
        id_board=1,  # placeholder: board padrão/simples, pode ser ajustado conforme regra de negócio
        responsavel_email=responsavel.email,
        titulo=task_in.title,
        descricao=task_in.description,
        status=task_in.status,
        tag=task_in.tag,
        data_inicio=task_in.startDate,
        data_fim=task_in.endDate,
        dependencia_id=dependencia.id_tarefa if dependencia else None,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


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

    task_db.titulo = task_in.title
    task_db.descricao = task_in.description
    task_db.status = task_in.status
    task_db.tag = task_in.tag
    task_db.data_inicio = task_in.startDate
    task_db.data_fim = task_in.endDate
    task_db.responsavel_email = responsavel.email
    task_db.dependencia_id = dependencia.id_tarefa if dependencia else None

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
