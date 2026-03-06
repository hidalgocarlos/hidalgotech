import os

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..models.calculo import Base, CalculoROI

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "roi.db")
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


class ROIDAO:
    def save(self, inversion: float, ventas: float, roi_pct: float, roas: float,
             clics: int, conversiones: int, cpc: float, cpa: float, username: str):
        with SessionLocal() as db:
            try:
                c = CalculoROI(
                    inversion=inversion,
                    ventas=ventas,
                    roi_pct=roi_pct,
                    roas=roas,
                    clics=clics,
                    conversiones=conversiones,
                    cpc=cpc,
                    cpa=cpa,
                    username=username,
                )
                db.add(c)
                db.commit()
            except Exception:
                db.rollback()
                raise

    def get_recent(self, limit: int = 50):
        with SessionLocal() as db:
            return db.query(CalculoROI).order_by(CalculoROI.created_at.desc()).limit(limit).all()
