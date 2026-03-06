import os

from sqlalchemy import create_engine
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..models.download import Base, Download

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "instagram.db")
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
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


listen(engine, "connect", _set_sqlite_pragma)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class DownloadDAO:
    def save(
        self,
        url: str,
        filename: str,
        title: str,
        uploader: str,
        duration: int,
        file_size: int,
        media_type: str,
        username: str,
    ):
        with SessionLocal() as db:
            try:
                download = Download(
                    url=url,
                    filename=filename,
                    title=title,
                    uploader=uploader,
                    duration=duration,
                    file_size=file_size,
                    media_type=media_type,
                    username=username,
                )
                db.add(download)
                db.commit()
            except Exception:
                db.rollback()
                raise

    def get_recent(self, limit: int = 50):
        with SessionLocal() as db:
            return (
                db.query(Download)
                .order_by(Download.downloaded_at.desc())
                .limit(limit)
                .all()
            )

    def get_by_id(self, id: int):
        with SessionLocal() as db:
            return db.query(Download).filter(Download.id == id).first()
