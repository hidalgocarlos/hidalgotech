from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Margen(Base):
    __tablename__ = "margenes"
    id = Column(Integer, primary_key=True)
    coste_producto = Column(Float, nullable=False)
    envio = Column(Float, default=0)
    fee_plataforma_pct = Column(Float, default=0)
    impuesto_pct = Column(Float, default=0)
    precio_venta = Column(Float, nullable=False)
    margen_neto = Column(Float, nullable=False)
    margen_pct = Column(Float)
    cpa = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    username = Column(String)
