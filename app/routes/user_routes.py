from fastapi import APIRouter, Depends, HTTPException, status # Importe 'status'
from sqlalchemy.orm import Session
from app import models, schemas, security
from app.database import get_db
from app import crud
import secrets
from app.database import redis_client
import requests
import os


router = APIRouter(prefix="/usuarios", tags=["Usuários"])
RESET_TOKEN_EXPIRATION_SECONDS = 600

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_FROM_EMAIL = os.getenv("BREVO_FROM_EMAIL", "noreply@clariatask.shop")
BREVO_FROM_NAME = os.getenv("BREVO_FROM_NAME", "Equipe ClarIA")


def send_reset_email(email: str, token: str):
    subject = "Redefinição de senha"
    html_content = f"""
    <html>
    <body>
        <h2>Redefinição de senha</h2>
        <p>Olá,</p>
        <p>Você solicitou a redefinição de senha.</p>
        <p><strong>Use este token para redefinir sua senha:</strong> {token}</p>
        <p>Se não foi você, ignore este e-mail.</p>
        <br>
        <p>Equipe ClarIA</p>
    </body>
    </html>
    """

    payload = {
        "sender": {
            "name": BREVO_FROM_NAME,
            "email": BREVO_FROM_EMAIL
        },
        "to": [
            {
                "email": email
            }
        ],
        "subject": subject,
        "htmlContent": html_content
    }

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    response = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        json=payload,
        headers=headers
    )

    if response.status_code not in [200, 201]:
        raise Exception(f"Brevo API error: {response.status_code} - {response.text}")

    return response.json()


@router.post("/", response_model=schemas.Usuario)
def criar_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """
    Cria um novo usuário com senha criptografada.
    """
    # Verifica se o e-mail já existe
    usuario_existente = db.query(models.Usuario).filter(models.Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

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

    usuarios_formatados = [crud.build_user_out(u) for u in usuarios_db]

    return schemas.UserListResponse(users=usuarios_formatados)

@router.post("/reset-password-request")
def reset_password_request(data: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == data.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    token = secrets.token_urlsafe(48)
    redis_client.setex(f"reset:{token}", RESET_TOKEN_EXPIRATION_SECONDS, data.email)
    try:
        send_reset_email(data.email, token)
        return {"message": "E-mail de confirmação enviado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {str(e)}")

@router.post("/reset-password-confirm")
def reset_password_confirm(data: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    email = redis_client.get(f"reset:{data.token}")
    if not email:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado.")
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    senha = str(data.new_password)[:72]
    usuario.senha_hash = security.gerar_hash(senha)
    db.commit()
    redis_client.delete(f"reset:{data.token}")
    return {"message": "Senha redefinida com sucesso."}

@router.post("/board/set-dono")
def set_dono_board(data: schemas.SetDonoRequest, db: Session = Depends(get_db)):
    membro = db.query(models.BoardMembro).filter(
        models.BoardMembro.board_id == data.board_id,
        models.BoardMembro.usuario_email == data.usuario_email
    ).first()
    if not membro:
        raise HTTPException(status_code=404, detail="Usuário não é membro deste board.")
    membro.tag = "dono"
    db.commit()
    return {"message": f"Usuário {data.usuario_email} agora é dono do board {data.board_id}."}
