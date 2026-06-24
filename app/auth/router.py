from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.auth.models import User
from app.auth.schemas import LoginRequest, Token, UserCreate, UserResponse
from app.auth.utils import create_access_token, hash_password, verify_password
from app.database import get_db
from app.logging_config import get_logger
from app.schemas import ErrorResponse

router = APIRouter(prefix="/auth", tags=["auth"])
_auth_log = get_logger("appspec.auth")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    summary="Registrar novo usuário",
    responses={
        201: {"description": "Usuário criado com sucesso"},
        409: {
            "description": "Conflito — usuário ou e-mail já existe",
            "model": ErrorResponse,
        },
    },
    openapi_extra={"security": []},
)
async def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Registra um novo usuário com perfil **professional**.

    O username e email devem ser unicos. A senha e armazenada de forma
    segura (hash bcrypt).
    """
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=409, detail="Username ja existe")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email ja cadastrado")

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="professional",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Autenticar usuário",
    responses={
        200: {"description": "Login realizado com sucesso, retorna token JWT"},
        401: {
            "description": "Credenciais inválidas",
            "model": ErrorResponse,
        },
        403: {
            "description": "Usuário inativo",
            "model": ErrorResponse,
        },
    },
    openapi_extra={"security": []},
)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Autentica o usuário e retorna um **token JWT** de acesso.

    O token deve ser enviado no header `Authorization: Bearer <token>` para acessar
    os endpoints protegidos.
    """
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):  # type: ignore[arg-type]
        _auth_log.warning(f"Login falhou para usuario '{payload.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    if not user.is_active:
        _auth_log.warning(f"Login negado (usuario inativo) '{payload.username}'")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inativo",
        )
    token = create_access_token(data={"sub": user.username, "role": user.role})
    _auth_log.info(f"Login bem-sucedido para '{user.username}' (role={user.role})")
    return Token(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obter dados do usuário atual",
    responses={
        200: {"description": "Dados do usuário autenticado"},
        401: {"description": "Token não fornecido ou inválido"},
    },
)
async def me(current_user: User = Depends(get_current_user)):
    """Retorna os dados do usuário atualmente autenticado.

    Requer token JWT válido no header `Authorization`.
    """
    return current_user


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="Listar todos os usuários",
    responses={
        200: {"description": "Lista de usuários cadastrados"},
        403: {"description": "Acesso restrito a administradores"},
    },
)
async def list_users(
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Lista todos os usuários cadastrados no sistema.

    **Restrito a administradores.** Retorna dados públicos dos usuários.
    """
    return db.query(User).all()
