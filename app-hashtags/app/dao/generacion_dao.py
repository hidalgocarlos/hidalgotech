import os

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..models.generacion import Base, Generacion

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "hashtags.db")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)


def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


listen(engine, "connect", _set_sqlite_pragma)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class GeneracionDAO:
    def save(self, tema: str, red: str, copy_texto: str, hashtags: str, username: str):
        with SessionLocal() as db:
            try:
                g = Generacion(
                    tema=tema[:255],
                    red=red,
                    copy_texto=copy_texto[:5000] if copy_texto else None,
                    hashtags=hashtags[:2000] if hashtags else None,
                    username=username,
                )
                db.add(g)
                db.commit()
            except Exception:
                db.rollback()
                raise

    def get_recent(self, limit: int = 50):
        with SessionLocal() as db:
            return db.query(Generacion).order_by(Generacion.created_at.desc()).limit(limit).all()
