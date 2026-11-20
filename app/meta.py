"""
Meta tags de cada página: descripción, canonical, OpenGraph y Twitter.

Los manejadores arman un `PageMeta` y lo pasan como `meta` al template;
`partials/meta.html` lo pinta en el bloque `meta` de base.html. Las páginas de
error no lo reciben: llevan solo la descripción del sitio, sin canonical ni
tags sociales.

Todas las URLs salen de `templating.absolute_url`: con BLOG_BASE_URL, la URL
pública; sin ella, la del pedido.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import Request

from app.i18n import LANGS, OG_LOCALE, STRINGS, plain_text
from app.og import images
from app.templating import absolute_url, page_path


@dataclass(frozen=True)
class Image:
    url: str
    alt: str
    width: int = images.WIDTH
    height: int = images.HEIGHT


@dataclass(frozen=True)
class PageMeta:
    title: str
    description: str
    url: str                                  # canonical y og:url
    type: str                                 # og:type: "website" o "article"
    locale: str                               # og:locale
    image: Image
    locale_alternates: list[str] = field(default_factory=list)
    published_time: str | None = None         # article:published_time (ISO 8601, UTC)


def iso_utc(value: datetime) -> str:
    """Fecha del modelo (sin zona) como UTC explícita: «2026-11-14T10:00:00Z»."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _image_url(request: Request, path, version: str) -> str:
    static = page_path(request, "static", "es", path=images.static_path(path))
    return f"{absolute_url(request, static)}?v={version}"


def default_image(request: Request, lang: str) -> Image:
    """Imagen por defecto del idioma. Si todavía no se generó, la URL igual lleva la versión que tendrá."""
    path = images.default_image_path(lang)
    version = images.image_version(path) or images.fingerprint(images.default_fields(lang))
    description = plain_text(STRINGS[lang]["site_description"])
    return Image(_image_url(request, path, version), STRINGS[lang]["og_default_alt"].format(description=description))


def post_image(request: Request, post) -> Image:
    """La imagen del post; si todavía no tiene (o falló al generarse), la por defecto de su idioma."""
    path = images.post_image_path(post.slug)
    version = images.image_version(path)
    if version is None:
        return default_image(request, post.lang)
    return Image(_image_url(request, path, version), STRINGS[post.lang]["og_post_alt"].format(title=post.title))


def _canonical(request: Request) -> str:
    """La página pedida, sin query: los filtros y temas tienen su propia ruta."""
    return absolute_url(request, request.url.path)


def listing_meta(request: Request, lang: str, title: str, description: str) -> PageMeta:
    """Portada, archivo y tema: tipo sitio, imagen por defecto y el otro idioma como alternativa."""
    return PageMeta(
        title=title,
        description=description,
        url=_canonical(request),
        type="website",
        locale=OG_LOCALE[lang],
        locale_alternates=[OG_LOCALE[code] for code in LANGS if code != lang],
        image=default_image(request, lang),
    )


def post_meta(request: Request, post) -> PageMeta:
    """Un post: tipo artículo, su bajada, su imagen y la fecha de publicación."""
    return PageMeta(
        title=post.title,
        description=post.summary,
        url=_canonical(request),
        type="article",
        locale=OG_LOCALE[post.lang],
        image=post_image(request, post),
        published_time=iso_utc(post.published_at),
    )
