from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/boards", tags=["Boards"])

@router.post("/", response_model=schemas.BoardOut, status_code=201)
def create_board(board: schemas.BoardCreate, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    db_board = models.Board(nome=board.nome, usuario_email=user.email)
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    return schemas.BoardOut(id=db_board.id_board, nome=db_board.nome, usuario_email=db_board.usuario_email)

@router.get("/", response_model=schemas.BoardListResponse)
def list_boards(db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    boards = db.query(models.Board).filter(models.Board.usuario_email == user.email).all()
    return schemas.BoardListResponse(boards=[schemas.BoardOut(id=b.id_board, nome=b.nome, usuario_email=b.usuario_email) for b in boards])

@router.put("/{board_id}", response_model=schemas.BoardOut)
def update_board(board_id: int, board: schemas.BoardUpdate, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    db_board = db.query(models.Board).filter(models.Board.id_board == board_id, models.Board.usuario_email == user.email).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board não encontrado")
    db_board.nome = board.nome
    db.commit()
    db.refresh(db_board)
    return schemas.BoardOut(id=db_board.id_board, nome=db_board.nome, usuario_email=db_board.usuario_email)

@router.delete("/{board_id}", status_code=204)
def delete_board(board_id: int, db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)):
    db_board = db.query(models.Board).filter(models.Board.id_board == board_id, models.Board.usuario_email == user.email).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board não encontrado")
    db.delete(db_board)
    db.commit()
    return None

