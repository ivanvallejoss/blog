import re
from datetime import datetime

from sqlalchemy import CheckConstraint, String, Text, Integer, ForeignKey, DateTime, Boolean, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import expression
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Optional

from .base import Base
from ..render import markdown_to_text

SUMMARY_MAX = 160

# Bloques de markdown que no son un párrafo de texto: títulos, código, citas,
# listas, tablas, separadores y código sangrado.
_NOT_PARAGRAPH = re.compile(r"^(#|```|~~~|>|[-*+]\s|\d+\.\s|\||---|\*\*\*|    )")

class Post(Base):
    """
    Modelado de los Posts del blog - heredan directamente de la clase Base `./base.py`
    """
    __tablename__ = "posts"
    __table_args__ = (CheckConstraint("lang IN ('es', 'en')", name="ck_posts_lang"),)

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

    # Idioma del post (app/i18n.py · LANGS). Un post tiene uno solo: su
    # traducción, si existe, es otro post con su propio slug. Decide bajo qué
    # rutas se sirve (/… o /en/…) y en qué listados aparece.
    lang: Mapped[str] = mapped_column(
        String(2), nullable=False, index=True, default="es", server_default=text("'es'")
    )

    # Bajada escrita a mano (propiedad «Resumen» de Notion). Opcional: sin
    # ella, `summary` la deriva del primer párrafo.
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        Bajada del post (destacado de la portada, búsqueda, OpenGraph): la
        escrita a mano (`excerpt`) si existe; si no, el primer párrafo real,
        recortado a 160 caracteres.
        """
        if self.excerpt and self.excerpt.strip():
            return self.excerpt.strip()
        return self.derived_summary

    @property
    def derived_summary(self) -> str:
        """Primer párrafo de texto del markdown, recortado a 160 caracteres."""
        for block in self.content_markdown.split("\n\n"):
            if not block.strip() or _NOT_PARAGRAPH.match(block):
                continue
            # El conversor emite formato en línea y escapes: la bajada se
            # muestra como texto, así que se recorta sobre el texto plano.
            block = markdown_to_text(block.strip())
            if not block:
                continue
            if len(block) <= SUMMARY_MAX:
                return block
            # deja lugar para «…» dentro del límite
            return block[:SUMMARY_MAX - 1].rsplit(" ", 1)[0].rstrip(",;:—-") + "…"
        return ""
