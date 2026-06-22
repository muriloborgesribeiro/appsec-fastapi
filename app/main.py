import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import (
    BASE_DIR,
    CORS_ALLOW_CREDENTIALS,
    CORS_HEADERS,
    CORS_METHODS,
    CORS_ORIGINS,
    STATIC_DIR,
)

sys.path.insert(0, BASE_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.auth.models import User
    from app.auth.utils import hash_password
    from app.config import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_USERNAME
    from app.database import Base, SessionLocal, engine

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not existing:
            admin = User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                hashed_password=hash_password(ADMIN_PASSWORD),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
    from app.services.rag_service import get_document_store

    get_document_store().carregar()
    yield


tags_metadata = [
    {
        "name": "auth",
        "description": "Autenticação e gerenciamento de usuários. "
        "Registro, login e consulta de perfil.",
    },
    {
        "name": "diagnosticos",
        "description": "Diagnósticos de apendicite utilizando "
        "Escala de Alvarado, KNN e SVM. "
        "Operações de criação, listagem, consulta e remoção.",
    },
    {
        "name": "metricas",
        "description": "Métricas de desempenho dos modelos de Machine Learning "
        "(Acurácia, Precisão, Recall, F1-Score, matriz de confusão).",
    },
    {
        "name": "duvidas",
        "description": "Tira duvidas sobre o projeto usando RAG + Groq. "
        "Envia uma pergunta em linguagem natural e recebe resposta "
        "baseada na documentação.",
    },
    {
        "name": "health",
        "description": "Health check da aplicação.",
    },
]

app = FastAPI(
    title="APPSPEC API — Sistema de Apoio ao Diagnóstico de Apendicite",
    description="Backend API para o Sistema de Apoio ao "
    "Diagnóstico de Apendicite — UFG.\n\n"
    "Combina o escore clínico **Alvarado** com dois modelos de "
    "**Machine Learning** (KNN e SVM) treinados no dataset "
    "*Regensburg Pediatric Appendicitis* (UCI).\n\n"
    "## Autenticação\n\n"
    "A API utiliza **JWT Bearer Token**. Para acessar endpoints protegidos:\n"
    "1. Faça login em `POST /auth/login` com usuário e senha\n"
    "2. Copie o `access_token` retornado\n"
    "3. Clique no botão **Authorize** (canto superior direito) e "
    "insira o token no formato `Bearer <token>`\n\n"
    "## Perfis de Acesso\n\n"
    "- **admin**: Acesso total (criar, listar, deletar "
    "diagnósticos e gerenciar usuários)\n"
    "- **professional**: Pode criar e listar diagnósticos\n"
    "- **viewer**: Acesso somente leitura (listar diagnósticos e métricas)\n\n"
    "> Projeto didático para a disciplina **Agentes Inteligentes** — UFG.",
    version="1.2.0",
    lifespan=lifespan,
    contact={
        "name": "UFG — Agentes Inteligentes",
        "url": "https://ufg.br",
    },
    license_info={
        "name": "MIT License",
        "identifier": "MIT",
    },
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── OpenAPI Security Scheme ────────────────────────────────
from fastapi.openapi.utils import get_openapi


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        contact=app.contact,
        license_info=app.license_info,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Insira o token JWT no formato: **Bearer <token>**",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)


# ── Security Headers ────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net "
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net;"
        )
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ── Static files ───────────────────────────────────────────
if os.path.exists(STATIC_DIR):
    from fastapi.staticfiles import StaticFiles

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ── Routers ─────────────────────────────────────────────────
from app.auth import router as auth_router
from app.routers import api
from app.routers import duvidas as duvidas_router

app.include_router(api.router)
app.include_router(api.metricas_router)
app.include_router(duvidas_router.router)
app.include_router(auth_router.router)


# ── Health ──────────────────────────────────────────────────
@app.get("/health", tags=["health"], openapi_extra={"security": []})
async def health():
    """Health check da aplicação."""
    return {"status": "ok", "app": "appspec-fastapi"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8082, reload=True)
