from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Optional

from .base import Base

class Post(Base):
    """
    Modelado de los Posts del blog - heredan directamente de la clase Base `./base.py`
    """
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Propiedades sobre la sincronizacion de Notion
    notion_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Clave Foranea
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    # Relacion inversa
    category: Mapped["Category"] = relationship("Category", back_populates="posts")