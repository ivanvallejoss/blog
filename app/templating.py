from datetime import datetime

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from starlette.routing import NoMatchFound

from .config import LANG_SWITCH_ENABLED
from .dates import format_date, format_date_short
from .i18n import DEFAULT_LANG, LANGS, UI_TEXT, plural


def site_context(request: Request) -> dict:
    """
    Contexto común a todos los templates.

    `lang` queda fijo en español hasta la ventana de idioma; entonces sale de la
    ruta (/en/…) y este es el único lugar que cambia.
    """
    lang = DEFAULT_LANG
    try:
        rss_url = request.url_for("rss").path
    except NoMatchFound:
        rss_url = None  # el footer no muestra RSS hasta que exista la ruta

    return {
        "lang": lang,
        "langs": LANGS,
        "t": UI_TEXT[lang],
        "lang_switch_enabled": LANG_SWITCH_ENABLED,
        "current_year": datetime.now().year,
        "rss_url": rss_url,
    }


templates = Jinja2Templates(directory="app/templates", context_processors=[site_context])


@pass_context
def url_path_for(context: dict, name: str, /, **path_params) -> str:
    """
    `url_for` de los templates: solo la ruta («/concurrencia/»), nunca la URL
    absoluta. La de Starlette arma esquema y host con lo que llega en el pedido,
    y detrás del proxy eso puede ser http en una página https (links, CSS y JS).
    La navegación no depende de las cabeceras del proxy. Para una URL absoluta
    que sale del sitio (compartir, OpenGraph) usar config.BASE_URL.
    """
    return context["request"].url_for(name, **path_params).path


templates.env.globals["url_for"] = url_path_for

templates.env.filters["format_date"] = format_date
templates.env.filters["format_date_short"] = format_date_short
templates.env.filters["plural"] = plural
