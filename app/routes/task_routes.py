from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, crud
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    _usuario_logado=Depends(get_current_user),
):
    """
    Cria uma nova tarefa
    """
    try:
        task_db = crud.create_task(db, task_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return crud.build_task_out(task_db)


@router.put("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    task_in: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    _usuario_logado=Depends(get_current_user),
):
    """Atualiza tarefa existente."""
    task_db = crud.update_task(db, task_id, task_in)
    if not task_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada",
        )
    return crud.build_task_out(task_db)


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    _usuario_logado=Depends(get_current_user),
):
    """Remove uma tarefa."""
    ok = crud.delete_task(db, task_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada",
        )
    return {"message": "Tarefa excluída com sucesso"}


@router.get("/", response_model=schemas.TaskListResponse)
def list_tasks(
    db: Session = Depends(get_db),
    _usuario_logado=Depends(get_current_user),
):
    """Lista tarefas """
    tasks_db = crud.list_tasks(db)
    tasks_out = [crud.build_task_out(t) for t in tasks_db]
    return schemas.TaskListResponse(tasks=tasks_out)