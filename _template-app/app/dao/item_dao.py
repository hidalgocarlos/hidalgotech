from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models.item import Base, Item

DATABASE_URL = "sqlite:////app/data/template.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


class ItemDAO:
    def create(self, name: str, description: str = None):
        with SessionLocal() as db:
            item = Item(name=name, description=description)
            db.add(item)
            db.commit()

    def get_all(self, limit: int = 50):
        with SessionLocal() as db:
            return db.query(Item).order_by(Item.created_at.desc()).limit(limit).all()

    def get_by_id(self, id: int):
        with SessionLocal() as db:
            return db.query(Item).filter(Item.id == id).first()
