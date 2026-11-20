"""
Feed de cada idioma (`/rss.xml` y `/en/rss.xml`), en Atom (RFC 4287).

Por qué Atom y no RSS 2.0, aunque la URL se llame rss.xml (los lectores no
miran el nombre, miran el contenido):

- El feed lleva el post completo. Atom tiene `<content type="html">`. RSS 2.0
  solo tiene `<description>`, que la especificación deja ambiguo (¿resumen o
  texto completo? ¿escapado o no?), y para el texto completo hace falta la
  extensión `content:encoded`, de otro espacio de nombres.
- Atom exige un id permanente por entrada, `updated` y un link `self`. RSS 2.0
  los deja opcionales y cada lector los resuelve a su manera.
- Las fechas van en RFC 3339, con zona explícita. RSS 2.0 usa RFC 822, el
  formato del correo (días y meses en inglés, zonas abreviadas), que cada
  lector interpreta con distinta tolerancia.
- `xml:lang` marca el idioma del feed.

Se arma con `xml.etree.ElementTree`, que escapa el texto. El contenido es el
`content_html` ya renderizado, sin el ancla «#» de los títulos y con los links
y fuentes relativos convertidos en absolutos (un lector no conoce la URL de la
página).
"""
import html
import re
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from urllib.parse import urljoin

from app.i18n import STRINGS, plain_text, topic_name
from app.meta import iso_utc

ATOM_NS = "http://www.w3.org/2005/Atom"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
FEED_LIMIT = 20                      # entradas por feed, las más nuevas
MEDIA_TYPE = "application/atom+xml; charset=utf-8"

ET.register_namespace("", ATOM_NS)

# El ancla que agrega la extensión toc de Python-Markdown a cada h2/h3
# (app/render.py): <a class="headerlink" href="#id" title="…">#</a>.
_HEADERLINK = re.compile(r'<a class="headerlink"[^>]*>.*?</a>', re.S)
_URL_ATTR = re.compile(r'\b(href|src)="([^"]*)"')


def feed_html(content_html: str, page_url: str) -> str:
    """HTML de un post para el feed: sin anclas «#» y con todos los links absolutos."""
    content = _HEADERLINK.sub("", content_html)

    def absolute(match: re.Match) -> str:
        value = urljoin(page_url, html.unescape(match.group(2)))
        return f'{match.group(1)}="{html.escape(value, quote=True)}"'

    return _URL_ATTR.sub(absolute, content)


def _entry_id(post, page_url: str) -> str:
    """
    Id permanente de la entrada: el id de la página de Notion (un UUID), que no
    cambia si el post cambia de slug o de tema. Los posts sin UUID (los de
    muestra de seed-dev) usan su URL.
    """
    try:
        return uuid.UUID(post.notion_id).urn
    except (ValueError, AttributeError, TypeError):
        return page_url


def _updated(post) -> datetime:
    """Última edición en Notion (synced_at), nunca antes que la publicación."""
    return max(filter(None, (post.published_at, post.synced_at)))


def _sub(parent, tag: str, text: str | None = None, **attrs) -> ET.Element:
    element = ET.SubElement(parent, f"{{{ATOM_NS}}}{tag}", attrs)
    if text is not None:
        element.text = text
    return element


def build_feed(posts, lang: str, *, feed_url: str, home_url: str, icon_url: str, post_url) -> bytes:
    """
    Atom de `posts` (ya filtrados por idioma, del más nuevo al más viejo).
    `post_url(post)` da la URL absoluta de cada uno.
    """
    t = STRINGS[lang]
    posts = list(posts)[:FEED_LIMIT]

    feed = ET.Element(f"{{{ATOM_NS}}}feed", {XML_LANG: lang})
    _sub(feed, "title", t["feed_title"])
    _sub(feed, "subtitle", plain_text(t["site_description"]))
    _sub(feed, "link", rel="self", type="application/atom+xml", href=feed_url)
    _sub(feed, "link", rel="alternate", type="text/html", href=home_url)
    _sub(feed, "id", feed_url)
    updated = max((_updated(post) for post in posts), default=None)
    _sub(feed, "updated", iso_utc(updated) if updated else iso_utc(datetime.now(timezone.utc)))
    author = _sub(feed, "author")
    _sub(author, "name", t["author"])
    _sub(feed, "icon", icon_url)

    for post in posts:
        url = post_url(post)
        entry = _sub(feed, "entry")
        _sub(entry, "title", post.title)
        _sub(entry, "link", rel="alternate", type="text/html", href=url)
        _sub(entry, "id", _entry_id(post, url))
        _sub(entry, "published", iso_utc(post.published_at))
        _sub(entry, "updated", iso_utc(_updated(post)))
        _sub(entry, "category", term=post.category.slug, label=topic_name(post.category, lang))
        if post.summary:
            _sub(entry, "summary", post.summary)
        _sub(entry, "content", feed_html(post.content_html, url), type="html")

    return ET.tostring(feed, encoding="utf-8", xml_declaration=True)
