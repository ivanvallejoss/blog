"""
Flags de configuración del sitio, leídos del entorno una sola vez.
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# Switch ES/EN del header. Apagado hasta la ventana de idioma: no se muestra
# un control que todavía no hace nada (CORRECCIONES §4).
LANG_SWITCH_ENABLED = _flag("BLOG_LANG_SWITCH", default=False)

# Log de cada sentencia SQL (echo del engine). Apagado por defecto: llena la
# salida del servidor. Para depurar: BLOG_SQL_ECHO=1.
SQL_ECHO = _flag("BLOG_SQL_ECHO", default=False)

# URL pública del sitio, sin barra final (p. ej. https://blog.ivanvallejos.dev).
# Arma las URLs absolutas que salen del sitio: compartir un post (y, en la
# ventana de OpenGraph, og:url y og:image). Sin definir, se toman del pedido,
# que detrás de un proxy depende de sus cabeceras. Los links internos no la
# usan: son siempre solo la ruta (ver app/templating.py).
BASE_URL = os.environ.get("BLOG_BASE_URL", "").strip().rstrip("/") or None
