import time 
from pathlib import Path

import requests
import base64

from jose import jwt

from app.config import GITHUB_APP_CLIENT_ID, GITHUB_APP_PRIVATE_KEY_PATH

def gerar_github_app_jwt():
  private_key_path = Path(GITHUB_APP_PRIVATE_KEY_PATH)
  
  with open(private_key_path, "r") as private_key_file:
    private_key = private_key_file.read()
  
  now = int(time.time())
  
  payload = {
    "iat": now - 60,
    "exp": now + (10 * 60),
    "iss": GITHUB_APP_CLIENT_ID
  }
  
  token = jwt.encode(
    payload,
    private_key,
    algorithm="RS256"
  )
  
  return token

def gerar_installation_access_token(installation_id: int):
  app_jwt = gerar_github_app_jwt()
  
  headers = {
    "Authorization": f"Bearer {app_jwt}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  }
  
  response = requests.post(
    f"https://api.github.com/app/installations/{installation_id}/access_tokens",
    headers=headers,
  )
  
  response.raise_for_status()
  
  dados = response.json()
  
  return dados["token"]

def listar_repositorios(installation_id: int):
  token = gerar_installation_access_token(installation_id)
  
  headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  }
  
  response = requests.get(
    "https://api.github.com/installation/repositories",
    headers=headers,
  )
  
  response.raise_for_status()
  
  dados = response.json()
  
  return dados["repositories"]

def listar_conteudo_repositorio(installation_id: int, owner: str, repo: str, path: str = "", branch: str | None = None,):
  token = gerar_installation_access_token(installation_id)
  
  headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  }
  
  params = {}

  if branch:
      params["ref"] = branch
  
  response = requests.get(
    f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
    headers=headers,
    params=params,
  )
  
  response.raise_for_status()

  return response.json()

def obter_conteudo_arquivo(installation_id: int, owner: str, repo: str, path: str, branch: str | None = None,):
  token = gerar_installation_access_token(installation_id)
  
  headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  }
  
  params = {}

  if branch:
    params["ref"] = branch
  
  response = requests.get(
    f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
    headers=headers,
    params={"ref": branch}
  )
  
  response.raise_for_status()
  
  dados = response.json()
  
  conteudo_base64 = dados["content"]
  
  conteudo = base64.b64decode(conteudo_base64).decode("utf-8")
  
  return conteudo
  
  