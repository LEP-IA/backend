from fastapi import APIRouter, Depends, HTTPException
from app import models, security, schemas
from secrets import token_urlsafe
from app.database import redis_client
from app.services import github_service

from sqlalchemy.orm import Session
from app.database import get_db, redis_client

from urllib.parse import urlencode
from app.config import GITHUB_APP_SLUG

import requests
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix="/github",
    tags=["GitHub"],
)

GITHUB_STATE_EXPIRATION_SECONDS = 600


@router.get("/connect")
def github_connect(current_user: models.Usuario = Depends(security.get_current_user)):

    state = token_urlsafe(32)

    redis_client.setex(
        f"github:install_state:{state}",
        GITHUB_STATE_EXPIRATION_SECONDS,
        current_user.email,
    )

    params = urlencode({"state": state})

    install_url = (
        f"https://github.com/apps/" f"{GITHUB_APP_SLUG}/installations/new?{params}"
    )

    return {"install_url": install_url}


@router.get("/setup")
def github_setup(
    installation_id: int,
    state: str,
    setup_action: str | None = None,
    db: Session = Depends(get_db),
):

    redis_key = f"github:install_state:{state}"

    email = redis_client.get(redis_key)

    if not email:
        raise HTTPException(status_code=400, detail="State inválido ou expirado")

    try:
        dados_instalacao = github_service.obter_dados_instalacao(installation_id)

    except requests.HTTPError:
        raise HTTPException(
            status_code=400, detail="Instalação do GitHub inválida ou não acessível"
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=502, detail="Não foi possível comunicar com o GitHub"
        )

    account = dados_instalacao["account"]

    account_id = account["id"]
    account_login = account["login"]
    account_type = account["type"]

    repository_selection = dados_instalacao["repository_selection"]

    try:

        github_installation = (
            db.query(models.GitHubInstallation)
            .filter(models.GitHubInstallation.installation_id == installation_id)
            .first()
        )

        if not github_installation:
            github_installation = models.GitHubInstallation(
                installation_id=installation_id,
                account_id=account_id,
                account_login=account_login,
                account_type=account_type,
                repository_selection=repository_selection,
                created_by_email=email,
            )

            db.add(github_installation)

        else:
            github_installation.account_id = account_id
            github_installation.account_login = account_login
            github_installation.account_type = account_type
            github_installation.repository_selection = repository_selection

            if github_installation.created_by_email is None:
                github_installation.created_by_email = email

        db.commit()
        db.refresh(github_installation)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500, detail="Erro ao salvar a instalação do GitHub"
        )

    redis_client.delete(redis_key)

    return {
        "message": "GitHub conectado com sucesso",
        "installation_id": github_installation.installation_id,
        "account_login": github_installation.account_login,
        "account_type": github_installation.account_type,
    }


@router.get("/installations/{installation_id}/repositories")
def listar_repositorios_instalacao(
    installation_id: int,
    current_user: models.Usuario = Depends(security.get_current_user),
    db: Session = Depends(get_db),
):

    github_installation = (
        db.query(models.GitHubInstallation)
        .filter(models.GitHubInstallation.installation_id == installation_id)
        .first()
    )

    if not github_installation:
        raise HTTPException(
            status_code=404, detail="Instalação do GitHub não encontrada"
        )

    if github_installation.created_by_email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para gerenciar esta instalação",
        )

    try:
        repositorios = github_service.listar_repositorios(installation_id)

    except requests.HTTPError:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível acessar os repositórios desta instalação",
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=502, detail="Não foi possível comunicar com o GitHub"
        )

    repositorios_formatados = []

    for repo in repositorios:
        repositorios_formatados.append(
            {
                "id": repo["id"],
                "name": repo["name"],
                "full_name": repo["full_name"],
                "private": repo["private"],
                "default_branch": repo["default_branch"],
            }
        )

    return {
        "installation_id": installation_id,
        "repositories": repositorios_formatados,
    }


@router.post("/boards/{board_id}/repositories")
def associar_repositorio_board(
    board_id: int,
    dados: schemas.BoardRepositoryCreate,
    current_user: models.Usuario = Depends(security.get_current_user),
    db: Session = Depends(get_db),
):

    board = db.query(models.Board).filter(models.Board.id_board == board_id).first()

    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board não encontrado",
        )

    # Verifica se é o dono original do board
    is_owner_user = board.usuario_email == current_user.email

    # Verifica se é um membro que recebeu permissão de dono
    is_owner_member = (
        db.query(models.BoardMembro)
        .filter(
            models.BoardMembro.board_id == board_id,
            models.BoardMembro.usuario_email == current_user.email,
            models.BoardMembro.tag == "dono",
        )
        .first()
        is not None
    )

    # Se não for nenhum dos dois tipos de dono, bloqueia
    if not (is_owner_user or is_owner_member):
        raise HTTPException(
            status_code=403,
            detail="Apenas donos podem configurar repositórios neste Board",
        )

    # Existe uma GitHubInstallation cujo ID do GitHub é o que veio no JSON?
    github_installation = (
        db.query(models.GitHubInstallation)
        .filter(models.GitHubInstallation.installation_id == dados.installation_id)
        .first()
    )

    if not github_installation:
        raise HTTPException(
            status_code=404,
            detail="Instalação do GitHub não encontrada",
        )

    # verifica se essa conexão GitHub pode ser gerenciada pelo usuário atual
    if github_installation.created_by_email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail="Você não tem permissão para usar esta instalação do GitHub",
        )

    try:
        repositorios = github_service.listar_repositorios(dados.installation_id)

    except requests.HTTPError:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível acessar os repositórios desta instalação",
        )

    except requests.RequestException:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível comunicar com o GitHub",
        )

    repositorio = None

    for repo in repositorios:
        if repo["id"] == dados.repository_id:
            repositorio = repo
            break

    if not repositorio:
        raise HTTPException(
            status_code=404,
            detail="Repositório não encontrado nesta instalação do GitHub",
        )

    repositorio_ja_associado = (
        db.query(models.BoardRepository)
        .filter(
            models.BoardRepository.board_id == board_id,
            models.BoardRepository.repository_id == repositorio["id"],
        )
        .first()
    )

    if repositorio_ja_associado:
        raise HTTPException(
            status_code=409,
            detail="Este repositório já está associado ao Board",
        )

    board_repository = models.BoardRepository(
        board_id=board_id,
        github_installation_id=github_installation.id,
        repository_id=repositorio["id"],
        repository_name=repositorio["name"],
        repository_full_name=repositorio["full_name"],
        default_branch=repositorio["default_branch"],
        private=repositorio["private"],
    )

    try:
        db.add(board_repository)
        db.commit()
        db.refresh(board_repository)

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Erro ao associar repositório ao Board",
        )

    return {
        "message": "Repositório associado ao Board com sucesso",
        "repository": {
            "id": board_repository.id,
            "repository_id": board_repository.repository_id,
            "name": board_repository.repository_name,
            "full_name": board_repository.repository_full_name,
            "default_branch": board_repository.default_branch,
            "private": board_repository.private,
        },
    }
