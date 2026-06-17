from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

class SyncError(Base):
    """
    Modelado de los logs de errores de negocio del blog.
    """
    __tablename__ = "sync_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notion_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())