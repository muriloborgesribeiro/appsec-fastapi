from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Dados necessários para registrar um novo usuário."""

    username: str = Field(
        ..., min_length=3, max_length=50, description="Nome de usuário único"
    )
    email: str = Field(..., max_length=120, description="E-mail do usuário")
    password: str = Field(
        ..., min_length=6, max_length=100, description="Senha do usuário"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "joao.silva",
                "email": "joao.silva@email.com",
                "password": "segura123",
            }
        }
    }


class UserResponse(BaseModel):
    """Dados públicos de um usuário."""

    id: int
    username: str
    email: str
    role: str
    is_active: bool

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "username": "joao.silva",
                "email": "joao.silva@email.com",
                "role": "professional",
                "is_active": True,
            }
        },
    }


class LoginRequest(BaseModel):
    """Credenciais para autenticação."""

    username: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "joao.silva",
                "password": "segura123",
            }
        }
    }


class Token(BaseModel):
    """Token JWT retornado após autenticação."""

    access_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
            }
        }
    }


class TokenData(BaseModel):
    """Dados decodificados do token JWT."""

    username: str | None = None
    role: str | None = None
