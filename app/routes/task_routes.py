from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, crud, models
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/tarefas", tags=["Tasks"])

# Rota POST para CRIAR uma nova tarefa
@router.post("/", response_model=schemas.Tarefa, status_code=201)
def criar_tarefa(
    tarefa: schemas.TarefaCreate, 
    db: Session = Depends(get_db),
    # Adiciona a dependência JWT
    usuario_logado: models.Usuario = Depends(get_current_user) 
):
    """
    Cria uma nova tarefa no calendário, verificando a autorização do usuário logado.
    """
    # 1. Busca o board vinculado ao usuário logado
    board_usuario = db.query(models.Board).filter(
        models.Board.usuario_email == usuario_logado.email
    ).first()
    
    if not board_usuario:
        # Se o usuário logado não tiver um board (algo que deve ser criado no cadastro)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Nenhum board associado ao usuário."
        )

    # 2. VERIFICAÇÃO DE AUTORIZAÇÃO: Confirma se o id_board do payload corresponde ao id do usuário
    if tarefa.id_board != board_usuario.id_board:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Você só pode criar tarefas no seu próprio board."
        )
         
    try:
        db_tarefa = crud.create_task(db=db, task=tarefa)
        return db_tarefa
    except Exception as e:
        print(f"Erro ao criar tarefa na rota: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar a tarefa.")

# Rota GET para BUSCAR uma tarefa pelo ID (Também Protegida)
@router.get("/{id_tarefa}", response_model=schemas.Tarefa)
def buscar_tarefa(
    id_tarefa: int, 
    db: Session = Depends(get_db),
    usuario_logado: models.Usuario = Depends(get_current_user) # Adiciona proteção
):
    """
    Busca os detalhes de uma tarefa específica, garante a autorização.
    """
    db_tarefa = crud.get_task_by_id(db, task_id=id_tarefa)
    
    if db_tarefa is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
        
    # VERIFICAÇÃO DE AUTORIZAÇÃO (Mantida)
    board_usuario = db.query(models.Board).filter(
        models.Board.usuario_email == usuario_logado.email
    ).first()
    
    if not board_usuario or db_tarefa.id_board != board_usuario.id_board:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Você não tem acesso a esta tarefa."
        )
    
    # 4. RESPOSTA: Converte o objeto do DB para o Schema de resposta
    tarefa_response = schemas.Tarefa.model_validate(db_tarefa)
    return tarefa_response