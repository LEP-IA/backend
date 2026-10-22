from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_current_user

router = APIRouter(
    prefix="/boards",
    tags=["Perfil no Board"],
)


# Consultar perfil profissional do usuário dentro do board
@router.get(
    "/{board_id}/me/profile",
    response_model=schemas.BoardMembroPerfilOut,
)
def obter_perfil_membro(
    board_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    board = db.query(models.Board).filter(models.Board.id_board == board_id).first()

    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board não encontrado",
        )

    membro = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == usuario.email,
        )
        .first()
    )

    if not membro:
        raise HTTPException(
            status_code=403,
            detail="Você não é membro deste board",
        )

    return membro


# Atualizar perfil profissional do usuário dentro do board
@router.put(
    "/{board_id}/me/profile",
    response_model=schemas.BoardMembroPerfilOut,
)
def atualizar_perfil_membro(
    board_id: int,
    dados: schemas.BoardMembroPerfilUpdate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    board = db.query(models.Board).filter(models.Board.id_board == board_id).first()

    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board não encontrado",
        )

    membro = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == usuario.email,
        )
        .first()
    )

    if not membro:
        raise HTTPException(
            status_code=403,
            detail="Você não é membro deste board",
        )

    membro.project_role = dados.project_role
    membro.participation_type = dados.participation_type
    membro.weekly_hours = dados.weekly_hours

    db.commit()
    db.refresh(membro)

    return membro
