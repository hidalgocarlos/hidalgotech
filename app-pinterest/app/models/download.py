from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Download(Base):
    __tablename__ = "downloads"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    title = Column(String)
    uploader = Column(String)
    duration = Column(Integer)
    file_size = Column(BigInteger)
    downloaded_at = Column(DateTime, default=datetime.utcnow)
    username = Column(String)
