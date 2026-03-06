import os

from sqlalchemy import create_engine, text
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..models.margen import Base, Margen

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "margen.db")
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


def _ensure_cpa_column():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE margenes ADD COLUMN cpa FLOAT DEFAULT 0"))
            conn.commit()
    except Exception:
        pass


_ensure_cpa_column()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class MargenDAO:
    def save(self, coste_producto: float, envio: float, fee_pct: float, impuesto_pct: float,
             precio_venta: float, margen_neto: float, margen_pct: float, username: str, cpa: float = 0):
        with SessionLocal() as db:
            try:
                m = Margen(
                    coste_producto=coste_producto,
                    envio=envio,
                    fee_plataforma_pct=fee_pct,
                    impuesto_pct=impuesto_pct,
                    precio_venta=precio_venta,
                    margen_neto=margen_neto,
                    margen_pct=margen_pct,
                    cpa=cpa,
                    username=username,
                )
                db.add(m)
                db.commit()
            except Exception:
                db.rollback()
                raise

    def get_recent(self, limit: int = 50):
        with SessionLocal() as db:
            return db.query(Margen).order_by(Margen.created_at.desc()).limit(limit).all()
