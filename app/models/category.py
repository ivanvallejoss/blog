from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from .base import Base


class Category(Base):
    """
    Category Model: 
    """
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # Relacion 1:N (posts tiene una categoria, una categoria tiene muchos posts)
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="category", cascade="all, delete-orphan")
