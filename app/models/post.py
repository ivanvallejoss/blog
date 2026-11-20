import re
from datetime import datetime

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Boolean, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import expression
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Optional

from .base import Base

SUMMARY_MAX = 160

class Post(Base):
    """
    Modelado de los Posts del blog - heredan directamente de la clase Base `./base.py`
    """
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[str] = mapped_column(Text, nullable=False)

    # Árbol de headings del post, derivado en el mismo paso que content_html.
    # Alimenta el bloque «En este artículo» del post (panel de lectura en
    # mobile, columna lateral en desktop).
    # Forma: [{"level": 2, "id": "el-preflight", "text": "El preflight"}, ...]
    content_toc: Mapped[list[dict]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )

    published_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=expression.false()
    )

    # Propiedades sobre la sincronizacion de Notion
    notion_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Clave Foranea
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    # Relacion inversa
    category: Mapped["Category"] = relationship("Category", back_populates="posts")


    @property
    def reading_minutes(self) -> int:
        """Minutos de lectura estimados: ~200 palabras/min sobre el
        markdown sin bloques de código (el código no se 'lee', se estudia)."""
        body = re.sub(r"```.*?```", "", self.content_markdown, flags=re.S)
        words = len(body.split())
        return max(1, round(words / 200))

    @property
    def summary(self) -> str:
        """
        Bajada del post (destacado de la portada, búsqueda, OpenGraph): primer
        párrafo real, recortado a 160 caracteres. Es una derivación, no una bajada editorial — el diseño pide
        el slot y el modelo no tiene el campo. Si más adelante querés escribir
        la bajada a mano, esto se reemplaza por una columna sincronizada desde
        Notion y el template no cambia.
        """
        for block in self.content_markdown.split("\n\n"):
            block = block.strip()
            if not block or block.startswith(("#", "```", ">", "-", "|", "*")):
                continue
            if len(block) <= SUMMARY_MAX:
                return block
            # deja lugar para «…» dentro del límite
            return block[:SUMMARY_MAX - 1].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"
        return ""