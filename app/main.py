import logging
import secrets
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import SessionLocal, engine
from .dates import MONTHS
from .i18n import DEFAULT_LANG, STRINGS, lang_from_path
from .routers import blog
from .selectors import get_recent_posts
from .templating import templates

logger = logging.getLogger("blog.errors")
# Bajo uvicorn el logger raíz no tiene salida: sin esto los errores con su
# referencia no llegarían al log del servidor.
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# «Quizás buscabas» de la 404: tres en desktop, dos en mobile (el tercero se
# oculta por CSS).
NOT_FOUND_RECENT = 3


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan)
app.include_router(blog.router)
app.mount("/static", StaticFiles(directory="static"), name="static")


def _error_ref() -> str:
    """Referencia corta para encontrar un error en el log: «7f3a-19nov-2241»."""
    now = datetime.now()
    month = MONTHS[DEFAULT_LANG][now.month - 1].lower()
    return f"{secrets.token_hex(2)}-{now.day:02d}{month}-{now:%H%M}"


# El idioma de una página de error sale de la ruta pedida, como el de
# cualquier página (app/i18n.py · lang_from_path): bajo /en/, en inglés. El
# contexto común de los templates lo deduce igual, así que la página entera
# (textos, <html lang>, switch) sale en ese idioma.

def _detail_text(detail, lang: str) -> str | None:
    """
    Los routers pasan en `detail` una clave del diccionario («post_not_found»).
    Cualquier otro detail (el «Not Found» de Starlette, por ejemplo) no se
    muestra: la página usa su texto por defecto.
    """
    if isinstance(detail, str) and detail in STRINGS[lang]:
        return STRINGS[lang][detail]
    return None


def _recent_posts_or_nothing(request: Request, lang: str) -> list:
    """
    Posts del idioma de la página para la 404. Si la base no responde, la
    página sale igual, sin ellos.
    """
    if request.url.path.startswith("/static/"):
        return []
    try:
        with SessionLocal() as db:
            return get_recent_posts(db, lang, limit=NOT_FOUND_RECENT)
    except Exception:
        logger.warning("404 sin «Quizás buscabas»: la base no respondió", exc_info=True)
        return []


def _retry_url(request: Request) -> str:
    """«Reintentar» como link a la misma ruta: funciona también sin JavaScript."""
    query = request.url.query
    return f"{request.url.path}?{query}" if query else request.url.path


def _error_page(request: Request, status_code: int, ref: str, headers=None):
    return templates.TemplateResponse(
        request,
        "errors/error.html",
        {"status_code": status_code, "ref": ref, "retry_url": _retry_url(request)},
        status_code=status_code,
        headers=headers,
    )


# La HTTPException de Starlette cubre también la de FastAPI y las que levanta
# el propio enrutador (una URL de tres segmentos, un método no permitido).
# Es síncrono a propósito: la 404 consulta la base y Starlette lo corre en el
# pool de hilos, sin bloquear el loop.
@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        lang = lang_from_path(request.url.path)
        return templates.TemplateResponse(
            request,
            "errors/404.html",
            {"detail": _detail_text(exc.detail, lang), "recent": _recent_posts_or_nothing(request, lang)},
            status_code=404,
            headers=exc.headers,
        )
    ref = _error_ref()
    level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    logger.log(level, "HTTP %s [ref %s] en %s %s: %s",
               exc.status_code, ref, request.method, request.url.path, exc.detail)
    return _error_page(request, exc.status_code, ref, headers=exc.headers)


# Excepciones no controladas: 500 con la plantilla genérica. No toca la base.
# La referencia que ve el lector queda en el log junto con la traza.
@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    ref = _error_ref()
    logger.error("Error no controlado [ref %s] en %s %s",
                 ref, request.method, request.url.path, exc_info=exc)
    return _error_page(request, 500, ref)
