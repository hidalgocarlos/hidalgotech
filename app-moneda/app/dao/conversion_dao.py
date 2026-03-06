import os

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..models.conversion import Base, Conversion

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "moneda.db")
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


class ConversionDAO:
    def save(self, from_currency: str, to_currency: str, rate: float, amount: float, result: float, username: str):
        with SessionLocal() as db:
            try:
                c = Conversion(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=rate,
                    amount=amount,
                    result=result,
                    username=username,
                )
                db.add(c)
                db.commit()
            except Exception:
                db.rollback()
                raise

    def get_recent(self, limit: int = 50):
        with SessionLocal() as db:
            return db.query(Conversion).order_by(Conversion.created_at.desc()).limit(limit).all()

    def get_last_rate(self, from_currency: str, to_currency: str):
        with SessionLocal() as db:
            r = (
                db.query(Conversion)
                .filter(
                    Conversion.from_currency == from_currency.upper(),
                    Conversion.to_currency == to_currency.upper(),
                )
                .order_by(Conversion.created_at.desc())
                .first()
            )
            return r.rate if r else None
