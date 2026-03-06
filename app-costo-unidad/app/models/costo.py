from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class CostoUnidad(Base):
    __tablename__ = "costos"
    id = Column(Integer, primary_key=True)
    coste_total = Column(Float, nullable=False)
    unidades = Column(Integer, nullable=False)
    costo_por_unidad = Column(Float, nullable=False)
    nota = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    username = Column(String)
