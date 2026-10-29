from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app import models, schemas
from app.services import sprint_service
from app.database import get_db
from app.security import get_current_user
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/boards", tags=["Boards"])


class ConviteRequest(BaseModel):
    email: EmailStr


@router.post("/", response_model=schemas.BoardOut, status_code=201)
def create_board(
    board: schemas.BoardCreate,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user),
):
    db_board = models.Board(nome=board.nome, usuario_email=user.email)
    db.add(db_board)
    db.commit()
    db.refresh(db_board)
    # Adiciona o criador como dono
    from app import crud

    crud.add_board_member(db, db_board.id_board, user.email, tag="dono")
    # Monta lista de membros
    membros = (
        db.query(models.BoardMembro)
        .filter(models.BoardMembro.board_id == db_board.id_board)
        .all()
    )
    membros_out = [
        schemas.BoardMembroOut(usuario_email=m.usuario_email, tag=m.tag)
        for m in membros
    ]
    return schemas.BoardOut(
        id_board=db_board.id_board,
        nome=db_board.nome,
        membros=membros_out,
        sprint=sprint_service.montar_sprint_out(db_board),
    )


@router.get("/", response_model=schemas.BoardListResponse)
def list_boards(
    db: Session = Depends(get_db), user: models.Usuario = Depends(get_current_user)
):
    boards = (
        db.query(models.Board)
        .filter(
            or_(
                models.Board.usuario_email == user.email,
                models.Board.membros.any(
                    models.BoardMembro.usuario_email == user.email
                ),
            )
        )
        .all()
    )
    result = []
    for b in boards:
        membros = (
            db.query(models.BoardMembro)
            .filter(models.BoardMembro.board_id == b.id_board)
            .all()
        )
        membros_out = [
            schemas.BoardMembroOut(usuario_email=m.usuario_email, tag=m.tag)
            for m in membros
        ]
        result.append(
            schemas.BoardOut(
                id_board=b.id_board,
                nome=b.nome,
                membros=membros_out,
                sprint=sprint_service.montar_sprint_out(b),
            )
        )
    return schemas.BoardListResponse(boards=result)


@router.put("/{board_id}", response_model=schemas.BoardOut)
def update_board(
    board_id: int,
    board: schemas.BoardUpdate,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user),
):
    db_board = db.query(models.Board).filter(models.Board.id_board == board_id).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board não encontrado")

    is_owner_user = db_board.usuario_email == user.email
    is_owner_member = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == user.email,
            models.BoardMembro.tag == "dono",
        )
        .first()
        is not None
    )

    if not (is_owner_user or is_owner_member):
        raise HTTPException(
            status_code=403, detail="Apenas o dono pode atualizar o board"
        )

    db_board.nome = board.nome
    db.commit()
    db.refresh(db_board)
    membros = (
        db.query(models.BoardMembro)
        .filter(models.BoardMembro.board_id == db_board.id_board)
        .all()
    )
    membros_out = [
        schemas.BoardMembroOut(usuario_email=m.usuario_email, tag=m.tag)
        for m in membros
    ]
    return schemas.BoardOut(
        id_board=db_board.id_board,
        nome=db_board.nome,
        membros=membros_out,
        sprint=sprint_service.montar_sprint_out(db_board),
    )


@router.delete("/{board_id}", status_code=204)
def delete_board(
    board_id: int,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user),
):
    db_board = db.query(models.Board).filter(models.Board.id_board == board_id).first()
    if not db_board:
        raise HTTPException(status_code=404, detail="Board não encontrado")

    is_owner_user = db_board.usuario_email == user.email
    is_owner_member = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == user.email,
            models.BoardMembro.tag == "dono",
        )
        .first()
        is not None
    )

    if not (is_owner_user or is_owner_member):
        raise HTTPException(
            status_code=403, detail="Apenas o dono pode deletar o board"
        )

    db.delete(db_board)
    db.commit()
    return None


@router.post("/{board_id}/convidar", status_code=201)
def convidar_membro(
    board_id: int,
    convite: ConviteRequest,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user),
):
    from app import crud

    board = crud.get_board(db, board_id)
    if not board:
        raise HTTPException(status_code=404, detail="Board não encontrado")

    is_owner_user = board.usuario_email == user.email
    is_owner_member = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == user.email,
            models.BoardMembro.tag == "dono",
        )
        .first()
        is not None
    )

    if not (is_owner_user or is_owner_member):
        raise HTTPException(
            status_code=403, detail="Apenas o dono pode convidar membros"
        )

    usuario = crud.get_user_by_email(db, str(convite.email))
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não cadastrado")
    if crud.is_user_board_member(db, board_id, str(convite.email)):
        raise HTTPException(status_code=400, detail="Usuário já é membro do board")
    membro = crud.add_board_member(db, board_id, str(convite.email), tag="convidado")
    return {"message": f"Usuário {convite.email} convidado com sucesso"}


@router.delete("/{board_id}/membros/{usuario_email}", status_code=200)
def remover_membro_board(
    board_id: int,
    usuario_email: str,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user),
):
    board = db.query(models.Board).filter(models.Board.id_board == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board não encontrado")

    is_owner_user = board.usuario_email == user.email
    is_owner_member = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == user.email,
            models.BoardMembro.tag == "dono",
        )
        .first()
        is not None
    )

    if not (is_owner_user or is_owner_member):
        raise HTTPException(
            status_code=403, detail="Apenas o dono pode remover membros"
        )

    membro = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == usuario_email,
        )
        .first()
    )
    if not membro:
        raise HTTPException(status_code=404, detail="Usuário não é membro deste board.")
    db.delete(membro)
    db.commit()
    return {"message": f"Usuário {usuario_email} removido do board {board_id}."}

def _board_out(db: Session, board: models.Board) -> schemas.BoardOut:
    membros = (
        db.query(models.BoardMembro)
        .filter(models.BoardMembro.board_id == board.id_board)
        .all()
    )
    return schemas.BoardOut(
        id_board=board.id_board,
        nome=board.nome,
        membros=[
            schemas.BoardMembroOut(usuario_email=m.usuario_email, tag=m.tag)
            for m in membros
        ],
        sprint=sprint_service.montar_sprint_out(board),
    )


def _get_board_como_dono(
    db: Session, board_id: int, user: models.Usuario, acao: str
) -> models.Board:
    board = db.query(models.Board).filter(models.Board.id_board == board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board não encontrado")

    is_owner_user = board.usuario_email == user.email
    is_owner_member = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == user.email,
            models.BoardMembro.tag == "dono",
        )
        .first()
        is not None
    )
    if not (is_owner_user or is_owner_member):
        raise HTTPException(status_code=403, detail=f"Apenas o dono pode {acao}")
    return board


@router.post("/{board_id}/sprint/iniciar", response_model=schemas.BoardOut)
def iniciar_sprint(
    board_id: int,
    payload: schemas.SprintStart,
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user),
):
    board = _get_board_como_dono(db, board_id, user, "iniciar a sprint")
    try:
        sprint_service.iniciar_sprint(board, payload.duracao_dias, payload.inicio)
    except sprint_service.SprintError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    db.commit()
    db.refresh(board)
    return _board_out(db, board)


@router.post("/{board_id}/sprint/encerrar", response_model=schemas.BoardOut)
def encerrar_sprint(
    board_id: int,
    payload: schemas.SprintEnd | None = Body(default=None),
    db: Session = Depends(get_db),
    user: models.Usuario = Depends(get_current_user),
):
    board = _get_board_como_dono(db, board_id, user, "encerrar a sprint")
    try:
        sprint_service.encerrar_sprint(board, payload.fim if payload else None)
    except sprint_service.SprintError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    db.commit()
    db.refresh(board)
    return _board_out(db, board)