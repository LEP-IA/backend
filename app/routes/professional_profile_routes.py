from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas, security
from app.database import get_db

router = APIRouter(
    prefix="/usuarios",
    tags=["Perfil Profissional"],
)


# Consultar perfil profissional do usuário autenticado
@router.get("/me/professional-profile", response_model=schemas.PerfilProfissionalOut)
def obter_perfil_profissional(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(security.get_current_user),
):
    perfil = (
        db.query(models.PerfilProfissional)
        .filter(models.PerfilProfissional.usuario_email == usuario.email)
        .first()
    )

    if not perfil:
        return schemas.PerfilProfissionalOut()

    return perfil


# Criar ou atualizar perfil profissional
@router.put("/me/professional-profile", response_model=schemas.PerfilProfissionalOut)
def atualizar_perfil_profissional(
    dados: schemas.PerfilProfissionalUpdate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(security.get_current_user),
):
    perfil = (
        db.query(models.PerfilProfissional)
        .filter(models.PerfilProfissional.usuario_email == usuario.email)
        .first()
    )

    if not perfil:
        perfil = models.PerfilProfissional(usuario_email=usuario.email)
        db.add(perfil)

    perfil.area = dados.area
    perfil.profession = dados.profession
    perfil.specialization = dados.specialization
    perfil.role = dados.role
    perfil.seniority = dados.seniority
    perfil.experience_time = dados.experience_time

    db.commit()
    db.refresh(perfil)

    return perfil
