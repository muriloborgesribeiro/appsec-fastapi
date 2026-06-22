import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import BASE_DIR, STATIC_DIR, CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, CORS_METHODS, CORS_HEADERS

sys.path.insert(0, BASE_DIR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import SessionLocal, Base, engine
    from app.auth.models import User
    from app.auth.utils import hash_password
    from app.config import ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD

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
    yield


app = FastAPI(
    title="APPSPEC API — Sistema de Apoio ao Diagnóstico de Apendicite",
    description="Backend API para o Sistema de Apoio ao Diagnóstico de Apendicite — UFG",
    version="1.2.0",
    lifespan=lifespan,
)


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
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net;"
        )
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ── Static files ───────────────────────────────────────────
if os.path.exists(STATIC_DIR):
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ── Routers ─────────────────────────────────────────────────
from app.routers import api
from app.auth import router as auth_router
app.include_router(api.router)
app.include_router(auth_router.router)


# ── Health ──────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "app": "appspec-fastapi"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8082, reload=True)
