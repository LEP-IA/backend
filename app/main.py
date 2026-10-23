from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .routes import  user_routes
from app.routes import task_routes
from app.routes import ml_routes
from app.routes import board_routes
from app.routes import github_routes
from app.routes import professional_profile_routes
from app.routes import board_member_profile_routes
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware



# Cria a instância da aplicação FastAPI
app = FastAPI(title="ClarIA", version="0.1.0")

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

#Lista de origins permitidas
origins = [
    "https://frontend-production-3d2c3.up.railway.app",
    "https://claria-task.up.railway.app",
    "https://frontend-staging-4c50.up.railway.app",
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

@app.exception_handler(Exception)
async def unhandled_error(request: Request, _exc: Exception):
    """Garante CORS mesmo em 500; sem isso o browser mostra 'blocked by CORS'."""
    origin = request.headers.get("origin")
    response = JSONResponse(status_code=500, content={"detail": "Erro interno do servidor"})
    if origin in origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
    return response


app.include_router(user_routes.router)
app.include_router(task_routes.router)
app.include_router(ml_routes.router)
app.include_router(board_routes.router)  # Inclui as rotas de board
app.include_router(github_routes.router)
app.include_router(professional_profile_routes.router)
app.include_router(board_member_profile_routes.router)

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
