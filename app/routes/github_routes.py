from fastapi import APIRouter, Depends, HTTPException
from app import models, security
from secrets import token_urlsafe
from app.database import redis_client

from urllib.parse import urlencode
from app.config import GITHUB_APP_SLUG

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
        current_user.email
    )
    
    params = urlencode({"state": state})
    
    install_url = (
        f"https://github.com/apps/"
        f"{GITHUB_APP_SLUG}/installations/new?{params}"
    )
    
    return {
        "install_url": install_url
    }

@router.get("/setup")
def github_setup(installation_id: int, state: str, setup_action: str | None = None):
    
    redis_key = f"github:install_state:{state}"
    
    email = redis_client.get(redis_key)
    
    if not email:
        raise HTTPException(status_code=400, detail="State inválido ou expirado")
    
    
    return {
        "installation_id": installation_id,
        "setup_action": setup_action,
        "email": email,
    }
  
  

