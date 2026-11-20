"""
Índice de la búsqueda del cliente (`GET /search.json`, README §6 M4/D4).

Una entrada por post publicado, con lo que pide el README y, además, lo que el
cliente necesita para pintar una fila sin lógica propia: la ruta del post y la
fecha y los metadatos ya formateados en el idioma. El JavaScript no formatea
fechas ni arma URLs.

Solo los posts del idioma pedido (`/search.json?lang=`), con el nombre del
tema en ese idioma: buscar «concurrency» en inglés encuentra los de
«concurrencia». Las etiquetas de temas del cliente salen de este mismo campo.

La bajada sale de `Post.summary`, que renderiza markdown en cada lectura: con
unas decenas de posts no se nota (ver el informe de la ventana 4).
"""
from typing import Callable

from .dates import format_date_short
from .i18n import UI_TEXT, topic_name


def search_entry(post, lang: str, url: str) -> dict:
    t = UI_TEXT[lang]
    date_label = format_date_short(post.published_at, lang)
    minutes = t.minutes.format(n=post.reading_minutes)
    topic = topic_name(post.category, lang)
    return {
        "title": post.title,
        "slug": post.slug,
        "category": topic,
        "category_slug": post.category.slug,
        "excerpt": post.summary,
        "published_at": post.published_at.date().isoformat(),
        "reading_minutes": post.reading_minutes,
        "lang": post.lang,
        "url": url,
        "date_label": date_label,
        "meta_label": f"{date_label} · {topic} · {minutes}",
    }


def build_search_index(posts, lang: str, post_path: Callable) -> list[dict]:
    """
    `posts` en el orden en que se muestran (del más nuevo al más viejo); los
    de otro idioma se descartan. `post_path(post)` devuelve la ruta del post
    («/tema/slug/» o «/en/tema/slug/»).
    """
    return [search_entry(post, lang, post_path(post)) for post in posts if post.lang == lang]
