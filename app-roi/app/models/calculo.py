from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class CalculoROI(Base):
    __tablename__ = "calculos"
    id = Column(Integer, primary_key=True)
    inversion = Column(Float, nullable=False)
    ventas = Column(Float, nullable=False)
    roi_pct = Column(Float, nullable=False)
    roas = Column(Float, nullable=False)
    clics = Column(Integer)
    conversiones = Column(Integer)
    cpc = Column(Float)
    cpa = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    username = Column(String)
