import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..models.user import Base, User

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'portal.db')}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def _ensure_role_column():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'operador'"))
            conn.commit()
    except Exception:
        pass


def _ensure_is_active_column():
    """Añade is_active si no existe (migración para BDs antiguas)."""
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1"))
            conn.commit()
    except Exception:
        pass


_ensure_role_column()
_ensure_is_active_column()


class UserDAO:
    def get_by_username(self, username: str):
        with SessionLocal() as db:
            return db.query(User).filter(User.username == username).first()

    def create_user(self, username: str, hashed_password: str, role: str = "operador"):
        with SessionLocal() as db:
            user = User(
                username=username,
                hashed_password=hashed_password,
                role=role or "operador",
                is_active=1,
            )
            db.add(user)
            db.commit()

    def update_password(self, username: str, hashed_password: str):
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            if user:
                user.hashed_password = hashed_password
                db.commit()

    def update_role(self, username: str, role: str):
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            if user:
                user.role = role if role in ("admin", "operador") else "operador"
                db.commit()

    def delete_user(self, username: str) -> bool:
        """Elimina un usuario. Devuelve True si existía y se borró."""
        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            if user:
                db.delete(user)
                db.commit()
                return True
            return False

    def list_users(self):
        with SessionLocal() as db:
            return db.query(User).all()
