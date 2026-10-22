import os

from dotenv import load_dotenv


load_dotenv()


GITHUB_APP_CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID")
GITHUB_APP_CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET")
GITHUB_APP_SLUG = os.getenv("GITHUB_APP_SLUG")

GITHUB_APP_PRIVATE_KEY = os.getenv("GITHUB_APP_PRIVATE_KEY")
GITHUB_APP_PRIVATE_KEY_PATH = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")

FRONTEND_URL = os.getenv("FRONTEND_URL")

# Serviço prazo_model (previsão de prazo das tarefas). Sem a URL a previsão fica desligada.
PRAZO_MODEL_URL = (os.getenv("PRAZO_MODEL_URL") or "").strip() or None
PRAZO_MODEL_TIMEOUT = float(os.getenv("PRAZO_MODEL_TIMEOUT", "5"))