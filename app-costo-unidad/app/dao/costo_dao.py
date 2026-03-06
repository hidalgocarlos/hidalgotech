import os

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..models.costo import Base, CostoUnidad

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "costo_unidad.db")
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


class CostoDAO:
    def save(self, coste_total: float, unidades: int, costo_por_unidad: float, nota: str, username: str):
        with SessionLocal() as db:
            try:
                c = CostoUnidad(
                    coste_total=coste_total,
                    unidades=unidades,
                    costo_por_unidad=costo_por_unidad,
                    nota=nota or None,
                    username=username,
                )
                db.add(c)
                db.commit()
            except Exception:
                db.rollback()
                raise

    def get_recent(self, limit: int = 50):
        with SessionLocal() as db:
            return db.query(CostoUnidad).order_by(CostoUnidad.created_at.desc()).limit(limit).all()
