"""
Textos de interfaz por idioma.

Fuente: el objeto `strings` de `docs/design_handoff_blog_broadsheet/design/Blog 1a.dc.html`,
sin las claves que solo servían al prototipo (rótulos de pantallas de demo, pistas
como «toca Aa», el índice de ejemplo y el conteo fijo «7 posts · 3 temas»).
Las claves pasan de camelCase a snake_case. Lo que en el diseño era una función o
un texto armado con datos queda como plantilla con `{campos}` para `str.format`
(en Jinja: `t.results_many.format(n=3)`).

Las claves marcadas «fuera del diseño» las pide el blog real y el prototipo no
las trae (footer, accesibilidad, errores, lista vacía).

Regla: ningún texto de interfaz se escribe a mano en un template. Si falta uno,
se agrega acá en los dos idiomas.
"""

DEFAULT_LANG = "es"
LANGS = ("es", "en")

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
        "count_line": "{posts} posts · {topics} temas",
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
        "count_line": "{posts} posts · {topics} topics",
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
