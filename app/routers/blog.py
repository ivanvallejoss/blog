from fastapi import APIRouter, Depends, Request, HTTPException

from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import templates

from ..selectors import (
    get_archive_counts,
    get_category_by_slug,
    get_post_by_slugs,
    get_published_posts,
    get_tag_counts,
)

router = APIRouter()

@router.get("/")
def post_list(
    request: Request, 
    db: Session = Depends(get_db)
    ):
    posts = get_published_posts(db)
    return templates.TemplateResponse(
        request,
        "index.html", 
        {
            "posts": posts,
            "tags": get_tag_counts(db),
            "archive": get_archive_counts(db),
            "active_tag": None,
        }
        )


@router.get("/{category_slug}/")
def get_category(
    category_slug: str,
    request: Request,
    db: Session = Depends(get_db)
    ):
    category = get_category_by_slug(db, category_slug)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada o inexistente")

    return templates.TemplateResponse(
        request,
        "category.html",
        {
            "posts": category.posts,
            "category": category,
            "tags": get_tag_counts(db),
            "archive": get_archive_counts(db),
            "active_tag": category.slug,
        }
        )


@router.get("/{category_slug}/{post_slug}/")
def get_post(
    category_slug: str,
    post_slug: str,
    request: Request,
    db: Session = Depends(get_db)
    ):
    post = get_post_by_slugs(db, category_slug, post_slug)

    if not post:
        raise HTTPException(status_code=404, detail="Post no encontrado o categoria no encontrada")

    return templates.TemplateResponse(
        request,
        "post.html", 
        {"post": post}
        )