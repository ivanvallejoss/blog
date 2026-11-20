"""
Rutas de las páginas, por idioma, en un solo lugar.

Cada página tiene un nombre lógico (el que usan los templates en `url_for`) y
una ruta por idioma. El router la registra una vez por idioma con el nombre
`"{nombre}.{lang}"` (`archive.en`); `url_for('archive')` en un template elige
la del idioma en curso (ver app/templating.py). Las URLs en español son las de
siempre; las en inglés llevan el prefijo de LANG_PREFIX.

Orden de registro (lo resuelve `registration_order`): primero las rutas fijas
de los dos idiomas, después las de tema y post del inglés, y al final las del
español. `/{category_slug}/` captura cualquier ruta fija de un segmento, y
`/{category_slug}/{post_slug}/` captura `/en/{tema}/`: lo que va antes gana.
"""
from .i18n import LANG_PREFIX, LANGS

PAGES: dict[str, dict[str, str]] = {
    "post_list": {"es": "/", "en": "/en/"},
    "archive": {"es": "/archivo/", "en": "/en/archive/"},
    "get_category": {"es": "/{category_slug}/", "en": "/en/{category_slug}/"},
    "get_post": {"es": "/{category_slug}/{post_slug}/", "en": "/en/{category_slug}/{post_slug}/"},
    # Feed Atom de cada idioma (app/feed.py). Ruta fija: va antes que las de
    # tema, y «rss.xml» queda entre los slugs de tema reservados.
    "rss": {"es": "/rss.xml", "en": "/en/rss.xml"},
}

# Rutas sin idioma que viven en la raíz (el idioma va en la query).
UNLOCALIZED = ("/search.json",)


def route_name(name: str, lang: str) -> str:
    """Nombre registrado de una página en un idioma: «archive.en»."""
    return f"{name}.{lang}"


def is_page(name: str) -> bool:
    return name in PAGES


def registration_order() -> list[tuple[str, str, str]]:
    """
    [(nombre, lang, ruta), ...] en el orden en que hay que registrarlas: las
    fijas (sin parámetros) primero, después las de parámetros con prefijo de
    idioma y al final las que no lo tienen.
    """
    entries = [(name, lang, path) for name, paths in PAGES.items() for lang, path in paths.items()]

    def key(entry):
        _, lang, path = entry
        has_params = "{" in path
        return (has_params, not LANG_PREFIX[lang], path.count("/"))

    return sorted(entries, key=key)


def _reserved_topic_slugs() -> frozenset[str]:
    """
    Slugs de tema que chocan con una ruta fija: el primer segmento de cada ruta
    fija (después del prefijo de idioma), los prefijos de idioma, las rutas sin
    idioma y el montaje de estáticos. Un tema con uno de estos slugs queda
    tapado en al menos un idioma; el sync lo informa.
    """
    reserved = {"static"}
    reserved |= {prefix.strip("/") for prefix in LANG_PREFIX.values() if prefix}
    reserved |= {path.strip("/").split("/")[0] for path in UNLOCALIZED}
    for paths in PAGES.values():
        for lang, path in paths.items():
            if "{" in path:
                continue
            rest = path[len(LANG_PREFIX[lang]):].strip("/")
            if rest:
                reserved.add(rest.split("/")[0])
    return frozenset(reserved)


RESERVED_TOPIC_SLUGS = _reserved_topic_slugs()

assert set(LANGS) == {lang for paths in PAGES.values() for lang in paths}
