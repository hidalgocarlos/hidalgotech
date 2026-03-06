from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Generacion(Base):
    __tablename__ = "generaciones"
    id = Column(Integer, primary_key=True)
    tema = Column(String(255), nullable=False)
    red = Column(String(32), nullable=False)
    copy_texto = Column(Text)
    hashtags = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    username = Column(String)
