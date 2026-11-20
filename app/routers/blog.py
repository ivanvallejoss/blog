from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse

from sqlalchemy.orm import Session

from app.database import get_db
from app.i18n import lang_from_path, normalize_lang, other_lang
from app.search import build_search_index
from app.templating import absolute_url, page_path, templates
from app.urls import registration_order, route_name

from ..selectors import (
    count_posts,
    get_category_by_slug,
    get_next_post,
    get_post_by_slugs,
    get_posts_by_year,
    get_published_posts,
    get_recent_posts,
    get_tag_counts,
    group_posts_by_tag,
)

router = APIRouter()

# Filas de «Recientes» en desktop; en mobile se muestran todas (diseño 1a).
RECENT_DESKTOP = 4

# Tamaño de texto del artículo (README §8): entero en px, guardado por el
# cliente en localStorage. El template se lo pasa al script en línea del
# <head> y a static/js/article.js; el 18 por defecto es también el de
# --prose-size en blog-tokens.css, que es lo que se ve sin JavaScript.
TEXT_SIZE = {"min": 15, "max": 24, "default": 18, "key": "blog.textSize"}


def request_lang(request: Request) -> str:
    """Idioma de la página pedida, deducido de la ruta (app/i18n.py)."""
    return lang_from_path(request.url.path)


def post_path(request: Request, post) -> str:
    """Ruta de un post, bajo las de su idioma."""
    return page_path(
        request, "get_post", post.lang, category_slug=post.category.slug, post_slug=post.slug
    )


def _other_count(db: Session, lang: str, category_id=None) -> int:
    """
    Posts en el otro idioma, para el estado «sin posts en este idioma»: con
    más de cero, la página vacía ofrece ir a la misma página en el otro.
    """
    return count_posts(db, other_lang(lang), category_id)


# Rutas fijas registradas ANTES que /{category_slug}/ (CORRECCIONES §6). Las
# de las páginas, en los dos idiomas, las registra el bucle del final en el
# orden de app/urls.py.

# El índice cambia solo con un sync: unos minutos de caché alcanzan y evitan
# pedirlo de nuevo en cada página que abre la búsqueda.
SEARCH_CACHE = "public, max-age=300"


@router.get("/search.json", name="search_index")
def search_index(
    request: Request,
    lang: str | None = None,
    db: Session = Depends(get_db)
    ):
    lang = normalize_lang(lang)
    index = build_search_index(
        get_recent_posts(db, lang),
        lang,
        lambda post: post_path(request, post),
    )
    return JSONResponse(index, headers={"Cache-Control": SEARCH_CACHE})


def post_list(
    request: Request,
    lang: str = Depends(request_lang),
    db: Session = Depends(get_db)
    ):
    posts = get_published_posts(db, lang)
    tags = get_tag_counts(db, lang)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "featured": posts[0] if posts else None,
            "recent": posts[1:],
            "recent_desktop": RECENT_DESKTOP,
            "topics": group_posts_by_tag(posts, tags),
            "other_count": 0 if posts else _other_count(db, lang),
        }
        )


def _archive_response(request: Request, db: Session, lang: str, category=None):
    """
    Archivo completo o filtrado por tema, en `lang`: la misma plantilla y la
    página entera en los dos casos. HTMX recorta #listing, #archive-filters y
    el switch de idioma de la respuesta; el router no distingue pedidos de HTMX.
    """
    # Filtros: solo temas con al menos un post en el idioma (get_tag_counts).
    # El sync nunca borra temas, así que uno vacío no se ofrece como filtro;
    # entrar directo a su URL igual responde y muestra el estado vacío, sin
    # filtro marcado.
    tags = get_tag_counts(db, lang)
    category_id = category.id if category else None
    years = get_posts_by_year(db, lang, category_id)

    return templates.TemplateResponse(
        request,
        "archive.html",
        {
            "category": category,
            "active_tag": category.slug if category else None,
            "filters": tags,
            "years": years,
            "total_posts": sum(tag["count"] for tag in tags),
            "total_topics": len(tags),
            "other_count": 0 if years else _other_count(db, lang, category_id),
        }
        )


def archive(
    request: Request,
    lang: str = Depends(request_lang),
    db: Session = Depends(get_db)
    ):
    return _archive_response(request, db, lang)


def get_category(
    category_slug: str,
    request: Request,
    lang: str = Depends(request_lang),
    db: Session = Depends(get_db)
    ):
    # El tema existe o no en los dos idiomas a la vez: es el mismo slug. Uno
    # sin posts en este idioma responde con el estado vacío.
    category = get_category_by_slug(db, category_slug)
    if not category:
        # Un segmento que no es un tema puede ser cualquier cosa (un post mal
        # escrito, una ruta vieja): el texto genérico de la 404, como el diseño.
        raise HTTPException(status_code=404, detail="not_found_body")  # clave de app/i18n.py

    return _archive_response(request, db, lang, category)


def get_post(
    category_slug: str,
    post_slug: str,
    request: Request,
    lang: str = Depends(request_lang),
    db: Session = Depends(get_db)
    ):
    # Un post se sirve solo bajo las rutas de su idioma: bajo las del otro, 404.
    post = get_post_by_slugs(db, category_slug, post_slug, lang)

    if not post:
        raise HTTPException(status_code=404, detail="not_found_post")  # clave de app/i18n.py

    return templates.TemplateResponse(
        request,
        "post.html",
        {
            "post": post,
            "next_post": get_next_post(db, post),
            "share_url": absolute_url(request, post_path(request, post)),
            "text_size": TEXT_SIZE,
        }
        )


# Una ruta por página y por idioma («archive.es» → /archivo/, «archive.en» →
# /en/archive/), con el mismo manejador: el idioma lo deduce request_lang.
_HANDLERS = {
    "post_list": post_list,
    "archive": archive,
    "get_category": get_category,
    "get_post": get_post,
}
for _name, _lang, _path in registration_order():
    router.add_api_route(_path, _HANDLERS[_name], methods=["GET"], name=route_name(_name, _lang))
