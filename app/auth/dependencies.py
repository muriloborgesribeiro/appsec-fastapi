from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.utils import decode_token
from app.auth.models import User


def _decode_user_from_token(db: Session, token: str) -> User | None:
    payload = decode_token(token)
    if payload is None:
        return None
    username = payload.get("sub")
    if username is None:
        return None
    return db.query(User).filter(User.username == username).first()


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso necessario",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.removeprefix("Bearer ")
    user = _decode_user_from_token(db, token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inativo",
        )
    return user


def require_role(*roles: str):
    async def _role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inativo",
            )
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissao insuficiente",
            )
        return current_user
    return _role_checker
