from fastapi import APIRouter, Depends, HTTPException, status # Importe 'status'
from sqlalchemy.orm import Session
from app import models, schemas, security
from app.database import get_db
from app import crud
import secrets
from app.database import redis_client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


router = APIRouter(prefix="/usuarios", tags=["Usuários"])
RESET_TOKEN_EXPIRATION_SECONDS = 600

BREVO_SMTP_SERVER = os.getenv("BREVO_SMTP_SERVER", "smtp-relay.brevo.com")
BREVO_SMTP_PORT = int(os.getenv("BREVO_SMTP_PORT", 587))
BREVO_SMTP_USER = os.getenv("BREVO_SMTP_USER")
BREVO_SMTP_PASS = os.getenv("BREVO_SMTP_PASS")
BREVO_FROM_EMAIL = os.getenv("BREVO_FROM_EMAIL", BREVO_SMTP_USER)
BREVO_FROM_NAME = os.getenv("BREVO_FROM_NAME", "Equipe ClarIA")


def send_reset_email(email: str, token: str):
    subject = "Redefinição de senha"
    body = f"Olá,\n\nVocê solicitou a redefinição de senha.\n\nUse este token para redefinir sua senha: {token}\n\nSe não foi você, ignore este e-mail.\n\nEquipe Claria"

    msg = MIMEMultipart()
    msg["From"] = f"{BREVO_FROM_NAME} <{BREVO_FROM_EMAIL}>"
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(BREVO_SMTP_SERVER, BREVO_SMTP_PORT) as server:
        server.starttls()
        server.login(BREVO_SMTP_USER, BREVO_SMTP_PASS)
        server.sendmail(BREVO_FROM_EMAIL, email, msg.as_string())


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
