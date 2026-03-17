from fastapi import FastAPI

from .routes import  user_routes
from app.routes import task_routes
from fastapi.middleware.cors import CORSMiddleware



# Cria a instância da aplicação FastAPI
app = FastAPI(title="ClarIA", version="0.1.0")

#Lista de origins permitidas
origins = [
    # Também é preciso colocar a url do frontend de dev local
    "frontend-production-3d2c3.up.railway.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials = True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routes.router)
app.include_router(task_routes.router)

# Define um endpoint (ou "rota") para a raiz da **URL
@app.get("/")
def read_root():
    """
    Endpoint raiz que retorna uma mensagem de boas-vindas.
    """
    return {"message": "Bem-vindo à API do ClarIA!"}

# Endpoint para ver se a API está no ar
@app.get("/health")
def health_check():
    """
    Endpoint simples para verificar se a API está no ar.
    """
    return {"status": "ok"}