from fastapi import APIRouter, Depends, HTTPException, status # Importe 'status'
from sqlalchemy.orm import Session
from app import models, schemas, security
from app.database import get_db
from app import crud


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

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(user: schemas.SignupRequest, db: Session = Depends(get_db)):
    """Cadastro de usuário """
    name = user.name
    email = user.email
    password = user.password
    terms_accepted = user.termsAccepted

    if not terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="termsAccepted deve ser true",
        )

    existing = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado",
        )

    senha_hash = security.gerar_hash(password)
    novo_usuario = models.Usuario(email=email, nome=name, senha_hash=senha_hash)
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return {"message": "Usuário criado com sucesso"}

@router.post("/login", response_model=schemas.LoginResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Autenticação no padrão """
    email = data.email
    password = data.password

    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario or not security.verificar_senha(password, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )

    access_token = security.create_access_token(data={"email": usuario.email})

    user_out = schemas.UserOut(
        id=str(usuario.id_usuario) if hasattr(usuario, "id_usuario") else usuario.email,
        name=usuario.nome,
        email=usuario.email,
        avatarUrl=usuario.avatar_url if hasattr(usuario, "avatar_url") else None,
    )

    return schemas.LoginResponse(token=access_token, user=user_out)

@router.post("/logout")
def logout(
    _body: schemas.LogoutRequest,
    _current_user=Depends(security.get_current_user),
):
    """Logout stateless: apenas confirma a operação."""
    return {"message": "Logout realizado com sucesso."}


@router.get("/", response_model=schemas.UserListResponse)
def listar_usuarios(
        db: Session = Depends(get_db),
        _current_user=Depends(security.get_current_user)
):
    """
    Retorna a lista de todos os usuários no formato {"users": [...]}
    Requer autenticação.
    """
    usuarios_db = crud.list_users(db)

    # Usa o helper para converter cada usuário individualmente
    usuarios_formatados = [crud.build_user_out(u) for u in usuarios_db]

    return schemas.UserListResponse(users=usuarios_formatados)