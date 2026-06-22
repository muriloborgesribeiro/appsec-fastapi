import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import BASE_DIR

DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'db.sqlite3')}"

engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""), echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
