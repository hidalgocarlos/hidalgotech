from sqlalchemy import Column, Integer, String, DateTime, Text, Float
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Transcription(Base):
    __tablename__ = "transcriptions"
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    video_title = Column(String)
    source = Column(String, nullable=False)  # "subtitles" | "whisper"
    transcript = Column(Text)
    language = Column(String)
    duration_seconds = Column(Float, nullable=True)  # duración del vídeo en segundos
    created_at = Column(DateTime, default=datetime.utcnow)
    username = Column(String)
    status = Column(String, default="completed")  # "processing" | "completed" | "failed"
    error_message = Column(String, nullable=True)
