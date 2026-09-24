import time 
from pathlib import Path

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