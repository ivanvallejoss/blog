"""
Textos de interfaz por idioma.

Fuente: el objeto `strings` de `docs/design_handoff_blog_broadsheet/design/Blog 1a.dc.html`,
sin las claves que solo servían al prototipo (rótulos de pantallas de demo, pistas
como «toca Aa», el índice de ejemplo y el conteo fijo «7 posts · 3 temas»).
Las claves pasan de camelCase a snake_case. Lo que en el diseño era una función o
un texto armado con datos queda como plantilla con `{campos}` para `str.format`
(en Jinja: `t.results_many.format(n=3)`). Los pares `<clave>_one` / `<clave>_many`
se eligen con el filtro `plural`: `t | plural("posts", 7)` → «7 posts».

Las claves marcadas «fuera del diseño» las pide el blog real y el prototipo no
las trae (footer, accesibilidad, errores, lista vacía).

Regla: ningún texto de interfaz se escribe a mano en un template. Si falta uno,
se agrega acá en los dos idiomas.

Además viven acá las otras dos piezas de idioma que no son textos sueltos:
  lang_from_path(path)    el idioma de un pedido, deducido de su ruta (/en/…).
  topic_name(tema, lang)  el nombre visible de un tema en un idioma.
"""
from markupsafe import Markup, escape

DEFAULT_LANG = "es"
LANGS = ("es", "en")

# Prefijo de ruta de cada idioma. El idioma por defecto no lleva: sus URLs
# son las de siempre («/archivo/»); el inglés vive bajo /en/ (README §8).
LANG_PREFIX = {"es": "", "en": "/en"}

# Región de cada idioma para og:locale (ventana 6: español rioplatense, inglés
# de Estados Unidos).
OG_LOCALE = {"es": "es_AR", "en": "en_US"}

STRINGS: dict[str, dict[str, str]] = {
    "es": {
        # — del diseño —
        "archive": "Archivo",
        "featured": "Destacado",
        "recent": "Recientes",
        "see_archive": "Ver archivo completo",
        "search": "Buscar",
        "search_ph": "Buscar posts",
        "cancel": "Cancelar",
        "topics": "Temas",
        "back": "Volver",
        "next": "Siguiente",
        "reading_opts": "Opciones de lectura",
        "text_size": "Tamaño de texto",
        "share": "Compartir",
        "copy": "Copiar",
        "copied": "Copiado",
        "more": "Más",
        "in_article": "En este artículo",
        "read": "Leer artículo",
        "all": "Todo",
        "navigate": "navegar",
        "open": "abrir",
        "close": "cerrar",
        "all_posts": "Todos los posts",
        # countLine y res(n) del diseño, como plantillas
        # countLine del diseño, con singular y plural (ver el filtro `plural`)
        "posts_one": "1 post",
        "posts_many": "{n} posts",
        "topics_one": "1 tema",
        "topics_many": "{n} temas",
        "results_none": "Sin resultados",
        "results_one": "{n} resultado",
        "results_many": "{n} resultados",
        # — fuera del diseño —
        "site_title": "blog — Iván Vallejos",
        "author": "Iván Vallejos",
        "brand_mark": "IV",
        "brand_sub": "/blog",
        "search_kbd": "⌘K",
        "home": "Inicio",
        "skip_to_content": "Saltar al contenido",
        "main_nav": "Navegación principal",
        "language": "Idioma",
        "lang_es": "Español",
        "lang_en": "English",
        "landing_link": "ivanvallejos.dev ↗",
        "rss": "RSS",
        "copyright": "© {year} Iván Vallejos",
        "minutes": "{n} min",
        "no_posts": "Todavía no hay posts publicados.",
        "not_found_title": "Página no encontrada",
        "not_found_body": "El contenido que buscás no existe o fue movido.",
        "error_title": "Algo salió mal",
        "error_body": "Error inesperado. Intentá de nuevo en unos segundos; si sigue pasando, avisame.",
        "back_home": "Volver al inicio",
        "see_topic": "Ver los {n}",
        "empty_topic_title": "Todavía no hay posts sobre este tema",
        "empty_topic_body": "Probá con otro tema o mirá el archivo completo.",
        "load_failed": "No se pudo cargar el contenido.",
        "load_topic_failed": "No se pudo cargar el tema.",
        "retry": "Reintentar",
        "notifications": "Avisos",
        # artículo
        "text_smaller": "Achicar el texto",
        "text_larger": "Agrandar el texto",
        "text_smaller_mark": "A−",
        "text_larger_mark": "A+",
        "text_size_unit": "px",
        "linkedin": "LinkedIn",
        "share_on_linkedin": "Compartir en LinkedIn",
        "share_on_x": "Compartir en X",
        "link_copied": "Link copiado",
        "copy_failed": "No se pudo copiar el link.",
        "close_reading_opts": "Cerrar opciones de lectura",
        # búsqueda
        "search_results": "Resultados",
        "no_results_title": "Nada sobre «{q}» todavía",
        "no_results_body": "Probá con otra palabra o explorá por tema.",
        "search_failed": "No se pudo cargar la búsqueda.",
        "kbd_navigate": "↑↓",
        "kbd_open": "↵",
        "kbd_close": "esc",
        # errores (los routers pasan estas claves en `detail`)
        "not_found_post": "El post que buscás no existe o fue movido.",
        "maybe_looking": "Quizás buscabas",
        "error_ref": "ref · {ref}",
        # idioma
        "anchor_title": "Enlace a esta sección",
        "lang_empty_title": "Todavía no hay posts en español acá",
        "lang_empty_topic_one": "Hay 1 post sobre {topic} en inglés.",
        "lang_empty_topic_many": "Hay {n} posts sobre {topic} en inglés.",
        "lang_empty_all_one": "Hay 1 post en inglés.",
        "lang_empty_all_many": "Hay {n} posts en inglés.",
        # El botón del estado vacío lleva al otro idioma y se escribe en ese
        # idioma («Ver en español» en una página en inglés, como el diseño):
        # el template lo toma de la tabla del otro idioma.
        "see_in_this_lang": "Ver en español",
        # compartir y feed (ventana 6). `site_description` es la frase de la
        # imagen por defecto: lo que va entre asteriscos sale en itálica
        # (app/og/draw.py). Sin los asteriscos, es la descripción de la portada.
        "site_description": "Notas de Iván Vallejos sobre *concurrencia*, sistemas de diseño y la vida alrededor del código.",
        "archive_description": "Todos los posts del blog, por año y por tema.",
        "topic_description": "Posts sobre {topic} en el blog de Iván Vallejos.",
        "og_post_alt": "«{title}», en IV/blog",
        "og_default_alt": "IV/blog: {description}",
        "feed_title": "blog — Iván Vallejos · en español",
    },
    "en": {
        "archive": "Archive",
        "featured": "Featured",
        "recent": "Recent",
        "see_archive": "See full archive",
        "search": "Search",
        "search_ph": "Search posts",
        "cancel": "Cancel",
        "topics": "Topics",
        "back": "Back",
        "next": "Next",
        "reading_opts": "Reading options",
        "text_size": "Text size",
        "share": "Share",
        "copy": "Copy",
        "copied": "Copied",
        "more": "More",
        "in_article": "In this article",
        "read": "Read article",
        "all": "All",
        "navigate": "navigate",
        "open": "open",
        "close": "close",
        "all_posts": "All posts",
        "posts_one": "1 post",
        "posts_many": "{n} posts",
        "topics_one": "1 topic",
        "topics_many": "{n} topics",
        "results_none": "No results",
        "results_one": "{n} result",
        "results_many": "{n} results",
        "site_title": "blog — Iván Vallejos",
        "author": "Iván Vallejos",
        "brand_mark": "IV",
        "brand_sub": "/blog",
        "search_kbd": "⌘K",
        "home": "Home",
        "skip_to_content": "Skip to content",
        "main_nav": "Main navigation",
        "language": "Language",
        "lang_es": "Español",
        "lang_en": "English",
        "landing_link": "ivanvallejos.dev ↗",
        "rss": "RSS",
        "copyright": "© {year} Iván Vallejos",
        "minutes": "{n} min",
        "no_posts": "No posts published yet.",
        "not_found_title": "Page not found",
        "not_found_body": "The page you're looking for doesn't exist or was moved.",
        "error_title": "Something went wrong",
        "error_body": "Unexpected error. Try again in a few seconds; if it keeps happening, let me know.",
        "back_home": "Back to home",
        "see_topic": "See all {n}",
        "empty_topic_title": "No posts on this topic yet",
        "empty_topic_body": "Try another topic or browse the full archive.",
        "load_failed": "Couldn't load the content.",
        "load_topic_failed": "Couldn't load the topic.",
        "retry": "Retry",
        "notifications": "Notifications",
        "text_smaller": "Decrease text size",
        "text_larger": "Increase text size",
        "text_smaller_mark": "A−",
        "text_larger_mark": "A+",
        "text_size_unit": "px",
        "linkedin": "LinkedIn",
        "share_on_linkedin": "Share on LinkedIn",
        "share_on_x": "Share on X",
        "link_copied": "Link copied",
        "copy_failed": "Couldn't copy the link.",
        "close_reading_opts": "Close reading options",
        "search_results": "Results",
        "no_results_title": "Nothing about “{q}” yet",
        "no_results_body": "Try another word or browse by topic.",
        "search_failed": "Couldn't load search.",
        "kbd_navigate": "↑↓",
        "kbd_open": "↵",
        "kbd_close": "esc",
        "not_found_post": "The post you're looking for doesn't exist or was moved.",
        "maybe_looking": "Maybe you were looking for",
        "error_ref": "ref · {ref}",
        "anchor_title": "Link to this section",
        "lang_empty_title": "No posts in English here yet",
        "lang_empty_topic_one": "There is 1 post on {topic} in Spanish.",
        "lang_empty_topic_many": "There are {n} posts on {topic} in Spanish.",
        "lang_empty_all_one": "There is 1 post in Spanish.",
        "lang_empty_all_many": "There are {n} posts in Spanish.",
        "see_in_this_lang": "See in English",
        "site_description": "Notes by Iván Vallejos on *concurrency*, design systems and the life around code.",
        "archive_description": "Every post on the blog, by year and by topic.",
        "topic_description": "Posts about {topic} on Iván Vallejos’s blog.",
        "og_post_alt": "“{title}”, on IV/blog",
        "og_default_alt": "IV/blog: {description}",
        "feed_title": "blog — Iván Vallejos · in English",
    },
}

# Las dos tablas tienen que tener las mismas claves: falla al importar, no en producción.
assert STRINGS["es"].keys() == STRINGS["en"].keys(), (
    STRINGS["es"].keys() ^ STRINGS["en"].keys()
)


class UIText:
    """
    Vista de solo lectura de una tabla de STRINGS para los templates (`t`).

    No se pasa el dict directo porque Jinja resuelve `t.copy` como el método
    `dict.copy` antes que como la clave. Además, una clave inexistente falla con
    error en vez de renderizar vacío en silencio.
    """

    __slots__ = ("_table", "lang")

    def __init__(self, lang: str):
        self.lang = lang
        self._table = STRINGS[lang]

    def __getattr__(self, key: str) -> str:
        try:
            return self._table[key]
        except KeyError:
            raise KeyError(f"falta el texto de interfaz {key!r} en STRINGS[{self.lang!r}]") from None

    __getitem__ = __getattr__


UI_TEXT = {lang: UIText(lang) for lang in LANGS}


def plural(t: UIText, key: str, n: int, **fields) -> Markup:
    """
    Elige `<key>_one` o `<key>_many` y completa `{n}` y los demás `fields`.

    Devuelve Markup: el texto del diccionario se escapa y los campos también,
    salvo los que ya son Markup. Así un campo puede llevar marcado propio
    (`topic=Markup("<em>{}</em>").format(nombre)`) sin abrir la puerta a que un
    nombre que viene de Notion inyecte HTML.
    """
    template = getattr(t, f"{key}_one" if n == 1 else f"{key}_many")
    return Markup(escape(template)).format(n=n, **fields)


def plain_text(text: str) -> str:
    """Un texto del diccionario sin las marcas de énfasis (`*así*` → «así»)."""
    return text.replace("*", "")


def normalize_lang(value) -> str:
    """Un código de idioma conocido o el idioma por defecto."""
    return value if value in LANGS else DEFAULT_LANG


def other_lang(lang: str) -> str:
    """El otro idioma (el sitio tiene dos): el del switch y el del estado vacío."""
    return next(code for code in LANGS if code != lang)


def lang_from_path(path: str) -> str:
    """
    Idioma de un pedido según su ruta: «/en» y «/en/…» son inglés; todo lo
    demás, el idioma por defecto. Es el único lugar que lo decide: lo usan las
    rutas, el contexto común de los templates y los manejadores de error (una
    404 del enrutador no tiene ruta encontrada, pero sí path).
    """
    for lang, prefix in LANG_PREFIX.items():
        if prefix and (path == prefix or path.startswith(prefix + "/")):
            return lang
    return DEFAULT_LANG


# Nombres de los temas en cada idioma, indexados por el slug del tema. El slug
# es el mismo en los dos idiomas (/concurrencia/ y /en/concurrencia/); solo se
# traduce el nombre visible. Un tema que no está acá se muestra con su nombre
# original, el de Notion. El español no necesita entradas: los temas se
# escriben en Notion en español.
TOPIC_NAMES: dict[str, dict[str, str]] = {
    "es": {},
    "en": {
        "concurrencia": "concurrency",
        "herramientas": "tools",
    },
}


def topic_name(topic, lang: str) -> str:
    """
    Nombre visible de un tema en `lang`. `topic` es una Category o un dict con
    `slug` y `name` (como los de selectors.get_tag_counts).
    """
    if isinstance(topic, dict):
        slug, name = topic["slug"], topic["name"]
    else:
        slug, name = topic.slug, topic.name
    return TOPIC_NAMES.get(lang, {}).get(slug, name)
