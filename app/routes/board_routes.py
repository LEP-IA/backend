from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app import models, schemas
from app.database import get_db
from app.security import get_current_user
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/boards", tags=["Boards"])

class ConviteRequest(BaseModel):
    email: EmailStr

@router.post("/", response_model=schemas.BoardOut, status_code=201)
def create_board(board: schemas.BoardCreate, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    db_board = models.Board(nome=board.nome, usuario_email=user.email)
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    # Adiciona o criador como dono
    from app import crud
    crud.add_board_member(db, db_board.id_board, user.email, tag="dono")
    # Monta lista de membros
    membros = db.query(models.BoardMembro).filter(models.BoardMembro.board_id == db_board.id_board).all()
    membros_out = [schemas.BoardMembroOut(usuario_email=m.usuario_email, tag=m.tag) for m in membros]
    return schemas.BoardOut(id_board=db_board.id_board, nome=db_board.nome, membros=membros_out)

@router.get("/", response_model=schemas.BoardListResponse)
def list_boards(db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    boards = db.query(models.Board).filter(
        or_(
            models.Board.usuario_email == user.email,
            models.Board.membros.any(models.BoardMembro.usuario_email == user.email),
        )
    ).all()
    result = []
    for b in boards:
        membros = db.query(models.BoardMembro).filter(models.BoardMembro.board_id == b.id_board).all()
        membros_out = [schemas.BoardMembroOut(usuario_email=m.usuario_email, tag=m.tag) for m in membros]
        result.append(schemas.BoardOut(id_board=b.id_board, nome=b.nome, membros=membros_out))
    return schemas.BoardListResponse(boards=result)

@router.put("/{board_id}", response_model=schemas.BoardOut)
def update_board(board_id: int, board: schemas.BoardUpdate, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    db_board = db.query(models.Board).filter(and_(models.Board.id_board == board_id, models.Board.usuario_email == user.email)).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board não encontrado")
    db_board.nome = board.nome
    db.commit()
    db.refresh(db_board)
    membros = db.query(models.BoardMembro).filter(models.BoardMembro.board_id == db_board.id_board).all()
    membros_out = [schemas.BoardMembroOut(usuario_email=m.usuario_email, tag=m.tag) for m in membros]
    return schemas.BoardOut(id_board=db_board.id_board, nome=db_board.nome, membros=membros_out)

@router.delete("/{board_id}", status_code=204)
def delete_board(board_id: int, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    db_board = db.query(models.Board).filter(and_(models.Board.id_board == board_id, models.Board.usuario_email == user.email)).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board não encontrado")
    db.delete(db_board)
    db.commit()
    return None

@router.post("/{board_id}/convidar", status_code=201)
def convidar_membro(board_id: int, convite: ConviteRequest, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    from app import crud
    board = crud.get_board(db, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board não encontrado")
    if board.usuario_email != user.email:
        raise HTTPException(status_code=403, detail="Apenas o dono pode convidar membros")
    usuario = crud.get_user_by_email(db, str(convite.email))
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não cadastrado")
    if crud.is_user_board_member(db, board_id, str(convite.email)):
        raise HTTPException(status_code=400, detail="Usuário já é membro do board")
    membro = crud.add_board_member(db, board_id, str(convite.email), tag="convidado")
    return {"message": f"Usuário {convite.email} convidado com sucesso"}
