import os
import secrets
import re

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..models.link import Base, ShortLink

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "utm.db")
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

SLUG_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


def _random_slug():
    return secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8]


class LinkDAO:
    def create(self, long_url: str, slug: str = None, username: str = None) -> ShortLink:
        slug = (slug or "").strip().lower()
        if not slug:
            slug = _random_slug()
        if not SLUG_RE.match(slug):
            raise ValueError("Slug no válido (solo letras, números, - y _)")
        with SessionLocal() as db:
            try:
                if db.query(ShortLink).filter(ShortLink.slug == slug).first():
                    raise ValueError("Ese slug ya existe")
                link = ShortLink(slug=slug, long_url=long_url, username=username)
                db.add(link)
                db.commit()
                db.refresh(link)
                return link
            except ValueError:
                db.rollback()
                raise
            except Exception:
                db.rollback()
                raise

    def get_by_slug(self, slug: str):
        with SessionLocal() as db:
            return db.query(ShortLink).filter(ShortLink.slug == slug).first()

    def get_recent(self, limit: int = 50):
        with SessionLocal() as db:
            return db.query(ShortLink).order_by(ShortLink.created_at.desc()).limit(limit).all()
