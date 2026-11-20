from fastapi import APIRouter, Depends, Request, HTTPException

from sqlalchemy.orm import Session

from app.database import get_db
from app.templating import templates

from ..selectors import (
    get_category_by_slug,
    get_post_by_slugs,
    get_posts_by_year,
    get_published_posts,
    get_tag_counts,
    group_posts_by_tag,
)

router = APIRouter()

# Filas de «Recientes» en desktop; en mobile se muestran todas (diseño 1a).
RECENT_DESKTOP = 4


@router.get("/")
def post_list(
    request: Request,
    db: Session = Depends(get_db)
    ):
    posts = get_published_posts(db)
    tags = get_tag_counts(db)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "featured": posts[0] if posts else None,
            "recent": posts[1:],
            "recent_desktop": RECENT_DESKTOP,
            "topics": group_posts_by_tag(posts, tags),
        }
        )


def _archive_response(request: Request, db: Session, category=None):
    """
    Archivo completo o filtrado por tema: la misma plantilla y la página
    entera en los dos casos. HTMX recorta #listing y #archive-filters de la
    respuesta; el router no distingue pedidos de HTMX.
    """
    # Filtros: solo temas con al menos un post (get_tag_counts). El sync nunca
    # borra temas, así que uno vacío no se ofrece como filtro; entrar directo a
    # su URL igual responde y muestra el estado vacío, sin filtro marcado.
    tags = get_tag_counts(db)

    return templates.TemplateResponse(
        request,
        "archive.html",
        {
            "category": category,
            "active_tag": category.slug if category else None,
            "filters": tags,
            "years": get_posts_by_year(db, category.id if category else None),
            "total_posts": sum(tag["count"] for tag in tags),
            "total_topics": len(tags),
        }
        )


# Ruta fija registrada ANTES que /{category_slug}/ (CORRECCIONES §6).
@router.get("/archivo/", name="archive")
def archive(
    request: Request,
    db: Session = Depends(get_db)
    ):
    return _archive_response(request, db)


@router.get("/{category_slug}/")
def get_category(
    category_slug: str,
    request: Request,
    db: Session = Depends(get_db)
    ):
    category = get_category_by_slug(db, category_slug)
    if not category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada o inexistente")

    return _archive_response(request, db, category)


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
