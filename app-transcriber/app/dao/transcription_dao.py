import os

from sqlalchemy import create_engine, text
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..models.transcription import Base, Transcription

DATA_DIR = "/app/data"
DB_PATH = os.path.join(DATA_DIR, "transcriber.db")
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


def _ensure_status_columns():
    """Add status and error_message columns if they don't exist (existing DBs)."""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE transcriptions ADD COLUMN status VARCHAR DEFAULT 'completed'"))
            conn.commit()
        except Exception:
            conn.rollback()
        try:
            conn.execute(text("ALTER TABLE transcriptions ADD COLUMN error_message VARCHAR"))
            conn.commit()
        except Exception:
            conn.rollback()


def _ensure_duration_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE transcriptions ADD COLUMN duration_seconds FLOAT"))
            conn.commit()
        except Exception:
            conn.rollback()


_ensure_status_columns()
_ensure_duration_column()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class TranscriptionDAO:
    def save(
        self,
        url: str,
        video_title: str,
        source: str,
        transcript: str,
        language: str,
        username: str,
        duration_seconds: float = None,
    ):
        with SessionLocal() as db:
            try:
                t = Transcription(
                    url=url,
                    video_title=video_title,
                    source=source,
                    transcript=transcript or "",
                    language=language or "",
                    username=username,
                    status="completed",
                    duration_seconds=duration_seconds,
                )
                db.add(t)
                db.commit()
                return t.id
            except Exception:
                db.rollback()
                raise

    def create_pending(
        self,
        url: str,
        video_title: str,
        language: str,
        username: str,
        duration_seconds: float = None,
    ):
        with SessionLocal() as db:
            try:
                t = Transcription(
                    url=url,
                    video_title=video_title or "",
                    source="whisper",
                    transcript=None,
                    language=language or "",
                    username=username,
                    status="processing",
                    duration_seconds=duration_seconds,
                )
                db.add(t)
                db.commit()
                return t.id
            except Exception:
                db.rollback()
                raise

    def update_completed(self, id: int, transcript: str, source: str, duration_seconds: float = None):
        with SessionLocal() as db:
            try:
                t = db.query(Transcription).filter(Transcription.id == id).first()
                if t:
                    t.transcript = transcript or ""
                    t.source = source
                    t.status = "completed"
                    t.error_message = None
                    if duration_seconds is not None:
                        t.duration_seconds = duration_seconds
                    db.commit()
            except Exception:
                db.rollback()
                raise

    def update_failed(self, id: int, error_message: str):
        with SessionLocal() as db:
            try:
                t = db.query(Transcription).filter(Transcription.id == id).first()
                if t:
                    t.status = "failed"
                    t.error_message = error_message or ""
                    db.commit()
            except Exception:
                db.rollback()
                raise

    def get_recent(self, limit: int = 50):
        with SessionLocal() as db:
            return (
                db.query(Transcription)
                .order_by(Transcription.created_at.desc())
                .limit(limit)
                .all()
            )

    def get_by_id(self, id: int):
        with SessionLocal() as db:
            return db.query(Transcription).filter(Transcription.id == id).first()
