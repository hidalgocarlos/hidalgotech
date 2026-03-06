from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class ShortLink(Base):
    __tablename__ = "short_links"
    id = Column(Integer, primary_key=True)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    long_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    username = Column(String)
