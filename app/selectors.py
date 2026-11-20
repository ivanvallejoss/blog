from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from app.models.post import Post
from app.models.category import Category


def get_published_posts(db):
    """
    Obtiene todos los posts de la db ordenados por publicacion.
    Se hace un join de Category para poblar `post.category` por cada psot.
    """
    posts = db.query(
        Post
        ).options(
            joinedload(Post.category)
            ).order_by(
                    Post.featured.desc(),
                    Post.published_at.desc()
                ).all()
    
    return posts


def get_category_by_slug(db, slug):
    "Obtiene el objeto category y los posts relacionadas a este."
    category = db.query(
        Category
        ).options(
            selectinload(Category.posts)
            ).filter_by(
                slug=slug
                ).one_or_none()

    return category


def get_post_by_slugs(db, category_slug, post_slug):
    """
    Obtiene el post mediante su slug, 
    tambien filtra con category_slug para poblar post.category
    """
    post = db.query(
        Post
        ).join(
        Category
    ).options(
        joinedload(Post.category)
        ).filter(
            Category.slug == category_slug, Post.slug == post_slug
        ).one_or_none()

    return post


def get_tag_counts(db):
    """
    Grupo TAGS del rail: cada categoría con su cantidad de posts, más el
    total como entrada 'ALL'. 'ALL' lleva slug None — es lo que hace que
    el chequeo de activo en el template funcione sin un caso especial.
    """
    rows = (
        db.query(Category.name, Category.slug, func.count(Post.id))
        .join(Post, Post.category_id == Category.id)
        .group_by(Category.id)
        .order_by(func.count(Post.id).desc(), Category.name)
        .all()
    )

    tags = [{"name": name, "slug": slug, "count": count} for name, slug, count in rows]
    total = sum(tag["count"] for tag in tags)

    return [{"name": "ALL", "slug": None, "count": total}] + tags


def get_archive_counts(db):
    """
    Posts por año y mes: [{"year": 2026, "months": [{"month": 6, "count": 4}]}]
    Agrupado en SQL y agrupado por año en Python. El mes va como número: el
    rótulo depende del idioma y lo pone el template (`app.dates.month_label`).
    """
    year = func.extract("year", Post.published_at)
    month = func.extract("month", Post.published_at)

    rows = (
        db.query(year, month, func.count(Post.id))
        .group_by(year, month)
        .order_by(year.desc(), month.desc())
        .all()
    )

    groups = []
    for raw_year, raw_month, count in rows:
        y, m = int(raw_year), int(raw_month)
        if not groups or groups[-1]["year"] != y:
            groups.append({"year": y, "months": []})
        groups[-1]["months"].append({"month": m, "count": count})

    return groups