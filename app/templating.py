from datetime import datetime

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from markupsafe import Markup
from starlette.routing import NoMatchFound

from .config import BASE_URL, LANG_SWITCH_ENABLED
from .dates import format_date, format_date_short
from .i18n import LANGS, UI_TEXT, lang_from_path, other_lang, plain_text, plural, topic_name
from .urls import is_page, route_name

# Páginas que existen igual en los dos idiomas: el switch lleva a la misma
# página en el otro y llevan <link rel="alternate" hreflang>. Un post no (su
# traducción, si existe, es otro post sin vínculo) ni una página de error: el
# switch lleva a la portada del otro idioma.
EQUIVALENT_PAGES = ("post_list", "archive", "get_category")


def page_path(request: Request, name: str, lang: str, **path_params) -> str:
    """
    Ruta de una página en un idioma («/en/archive/»). `name` es el nombre
    lógico de app/urls.py (`archive`); cualquier otro nombre (`static`,
    `search_index`) se resuelve tal cual.
    """
    if is_page(name):
        name = route_name(name, lang)
    return request.url_for(name, **path_params).path


def absolute_url(request: Request, path: str) -> str:
    """
    URL absoluta de una ruta, para usar fuera del sitio (compartir, hreflang,
    canonical, OpenGraph y el feed). Con BLOG_BASE_URL se arma con ella;
    si no, sale del pedido (detrás de un proxy, da https solo si uvicorn
    confía en sus cabeceras).
    """
    base = BASE_URL or str(request.base_url).rstrip("/")
    return f"{base}{path}"


def _current_page(request: Request):
    """(nombre lógico, parámetros) de la página pedida, o None."""
    route = request.scope.get("route")
    name = getattr(route, "name", None) or ""
    base, _, lang = name.rpartition(".")
    if not is_page(base) or lang not in LANGS:
        return None
    return base, dict(request.path_params)


def site_context(request: Request) -> dict:
    """
    Contexto común a todos los templates.

    `lang` sale de la ruta (app/i18n.py · lang_from_path), igual que en los
    manejadores de error, que usan este mismo contexto.

    `lang_urls`: a dónde lleva el switch, por idioma: la misma página en
    portada, archivo y tema; la portada en un post. `lang_homes`: la portada de
    cada idioma (el switch de las páginas de error, que fijan
    {% set error_page = true %}). `hreflang`: [(idioma, URL absoluta)] de la
    página en cada idioma, o vacío si la página no tiene equivalente.
    """
    lang = lang_from_path(request.url.path)
    other = other_lang(lang)
    try:
        rss_url = request.url_for("rss").path
    except NoMatchFound:
        rss_url = None  # el footer no muestra RSS hasta que exista la ruta

    lang_homes = {code: page_path(request, "post_list", code) for code in LANGS}
    current = _current_page(request)
    if current and current[0] in EQUIVALENT_PAGES:
        name, params = current
        lang_urls = {code: page_path(request, name, code, **params) for code in LANGS}
        hreflang = [(code, absolute_url(request, path)) for code, path in lang_urls.items()]
    else:
        lang_urls = lang_homes
        hreflang = []

    return {
        "lang": lang,
        "other_lang": other,
        "langs": LANGS,
        "t": UI_TEXT[lang],
        # textos del otro idioma: el botón del estado vacío se escribe en el
        # idioma al que lleva («Ver en español» en una página en inglés)
        "t_other": UI_TEXT[other],
        "lang_switch_enabled": LANG_SWITCH_ENABLED,
        "lang_urls": lang_urls,
        "lang_homes": lang_homes,
        "hreflang": hreflang,
        "current_year": datetime.now().year,
        "rss_url": rss_url,
    }


templates = Jinja2Templates(directory="app/templates", context_processors=[site_context])


@pass_context
def url_path_for(context: dict, name: str, /, lang: str | None = None, **path_params) -> str:
    """
    `url_for` de los templates: solo la ruta («/concurrencia/»), nunca la URL
    absoluta. La de Starlette arma esquema y host con lo que llega en el pedido,
    y detrás del proxy eso puede ser http en una página https (links, CSS y JS).
    La navegación no depende de las cabeceras del proxy. Para una URL absoluta
    que sale del sitio (compartir, OpenGraph) usar `absolute_url`.

    Las páginas de app/urls.py se resuelven en el idioma en curso:
    `url_for('archive')` da «/archivo/» o «/en/archive/». Con `lang=` se pide
    la de otro idioma. Los templates no ramifican por idioma.
    """
    return page_path(context["request"], name, lang or context["lang"], **path_params)


def emphasis(value) -> Markup:
    """Texto entre <em>, escapado: para un campo de `plural` («on *life*»)."""
    return Markup("<em>{}</em>").format(value)


templates.env.globals["url_for"] = url_path_for

templates.env.filters["format_date"] = format_date
templates.env.filters["format_date_short"] = format_date_short
templates.env.filters["plural"] = plural
templates.env.filters["topic"] = topic_name
templates.env.filters["em"] = emphasis
templates.env.filters["plain"] = plain_text
