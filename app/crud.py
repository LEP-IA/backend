from sqlalchemy.orm import Session
from . import models, schemas

# CRUD para tarefas

def get_task_by_id(db: Session, task_id: int):
    """
    Busca uma tarefa específica pelo seu ID (id_tarefa)
    """
    return db.query(models.Tarefa).filter(models.Tarefa.id_tarefa == task_id).first()


def create_task(db: Session, task: schemas.TarefaCreate) -> models.Tarefa:
    """
    Cria uma nova Tarefa.
    """
    try:
        db_tarefa = models.Tarefa(
            id_board=task.id_board,
            nome=task.nome,
            local=task.local,
            duracao=task.duracao,
            hora_inicio=task.hora_inicio,
            hora_fim=task.hora_fim,
            local_de_saida=task.local_de_saida,
            transporte=task.transporte,
            distancia=task.distancia
        )
        db.add(db_tarefa)
        db.commit()
        db.refresh(db_tarefa)
        return db_tarefa
    except Exception as e:
        print(f"Erro ao criar tarefa: {e}")
        db.rollback()
        raise


def update_task_api_data(db: Session, id_tarefa: int, distancia: str, duracao: str):
    """
    Atualiza os dados de rota (distancia, duracao) de uma tarefa.
    """
    tarefa = db.query(models.Tarefa).filter(models.Tarefa.id_tarefa == id_tarefa).first()
    if tarefa:
        tarefa.distancia = distancia
        tarefa.duracao = duracao
        db.commit()
        db.refresh(tarefa)
    return tarefa