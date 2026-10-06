from fastapi import APIRouter, Depends, HTTPException
from app import models, security
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
            status_code=500,
            detail="Erro ao salvar a instalação do GitHub"
        )

    redis_client.delete(redis_key)

    return {
        "message": "GitHub conectado com sucesso",
        "installation_id": github_installation.installation_id,
        "account_login": github_installation.account_login,
        "account_type": github_installation.account_type,
    }
