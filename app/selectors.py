from sqlalchemy.orm import joinedload

from app.models.post import Post
from app.models.category import Category


def get_published_posts(db):
    """
    Obtiene todos los posts de la db ordenados por publicacion.
    Se hace un join de Category para poblar `post.category` por cada psot.
    """
    posts = db.Query(
        Post
        ).options(
            joinedload(Post.category)
            ).order_by(
                Post.published_at.desc()
                ).all()
    
    return posts


def get_category_by_slug(db, slug):
    "Obtiene el objeto category y los posts relacionadas a este."
    category = db.Query(
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
    post = db.Query(
        Post
        ).join(
        Category
    ).options(
        joinedload(Post.category)
        ).filter(
            Category.slug == category_slug, Post.slug == post_slug
        ).one_or_none()

    return post