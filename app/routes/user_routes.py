from fastapi import APIRouter, Depends, HTTPException, status # Importe 'status'
from sqlalchemy.orm import Session
from app import models, schemas, security, crud
from app.database import get_db


router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.post("/", response_model=schemas.Usuario)
def criar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """
    Cria um novo usuário com senha criptografada.
    """
    # Verifica se o e-mail já existe
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    # Criptografa a senha antes de salvar
    senha_hash = security.gerar_hash(usuario.senha)
    novo_usuario = models.Usuario(
        email=usuario.email,
        nome=usuario.nome,
        senha_hash=senha_hash
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@router.post("/login")
def login(login_data: schemas.UsuarioLogin, db: Session = Depends(get_db)):

    """

    Faz login verificando o hash da senha, usando um JSON no corpo da requisição.

    """

    # Acessa os dados através do objeto login_data

    usuario = db.query(models.Usuario).filter(models.Usuario.email == login_data.email).first()


    if not usuario or not security.verificar_senha(login_data.senha, usuario.senha_hash):

        # Unifique as mensagens para evitar dar dicas sobre se o usuário existe ou se a senha está errada

        raise HTTPException(

            status_code=status.HTTP_401_UNAUTHORIZED,

            detail="E-mail ou senha incorretos."

        )

    # 1. Cria o token de acesso

    access_token = security.create_access_token(

        data={"email": usuario.email}

    )

    # 2. Retorna o token e o tipo (padrão Bearer)

    return {

        "access_token": access_token,

        "token_type": "bearer",

        "usuario": schemas.Usuario.model_validate(usuario)

    }

@router.get("/me", response_model=schemas.UsuarioResponseCompleto)
def get_meus_dados_completos(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(security.get_current_user)
):
    """
    Endpoint protegido para "recarregar" o perfil.
    
    Retorna todos os dados do usuário logado (perfil, calendários e
    todos os eventos aninhados com seus transportes, datas, etc.).
    """
    
    # A dependência 'get_current_user' já nos dá o usuário
    # Mas esse usuário NÃO tem os dados aninhados carregados.
    
    # Usamos a função do CRUD para buscar o usuário DE NOVO,
    # mas desta vez com todos os dados.
    usuario_data = crud.get_user_full_data(db, email=current_user.email)
    
    if not usuario_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuário não encontrado."
        )
        
    return usuario_data