from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class QRLog(Base):
    __tablename__ = "qr_logs"
    id = Column(Integer, primary_key=True)
    content = Column(String(2048), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    username = Column(String)
