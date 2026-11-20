"""
Archivos de las imágenes para compartir: cuándo se generan, dónde viven y con
qué versión se piden.

    static/og/{slug}.png          imagen de cada post (Post.slug es único en
                                  toda la tabla: sirve igual en los dos idiomas)
    static/og/default/{lang}.png  imagen por defecto de cada idioma

`static/og/` no se commitea: la llenan el sync, `cli.py og-images` y
`cli.py seed-dev`.

**Huella.** Todo lo que la imagen muestra (título, tema, fila de autor, fecha y
minutos, dominio, frase) más RENDER_VERSION se resume en una huella. La huella
viaja dentro del mismo PNG, en un chunk de texto antes de los píxeles. Así:

- regenerar o no se decide comparando la huella esperada con la guardada, sin
  columna en la base y sin archivos aparte;
- la URL de la imagen lleva `?v={huella}`: cambia exactamente cuando cambia la
  imagen, y Cloudflare y las redes, que cachean por URL, piden la nueva.

Si cambia el código de dibujo o una fuente, subir RENDER_VERSION: cambia la
huella de todas y la próxima pasada las regenera.
"""
import hashlib
import json
import logging
import os
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, PngImagePlugin

from app import config
from app.dates import format_date
from app.i18n import LANGS, STRINGS, topic_name

from . import draw, tokens

logger = logging.getLogger(__name__)

RENDER_VERSION = 1
OG_DIR = Path("static/og")
_FINGERPRINT_KEY = "blog-og"
_VERSION_LENGTH = 12

WIDTH, HEIGHT = tokens.OG_WIDTH, tokens.OG_HEIGHT


# ── Qué muestra cada imagen ──────────────────────────────────────────────

def site_domain() -> str:
    """Dominio de la fila inferior, de BLOG_BASE_URL. Sin ella, vacío (y la imagen sale sin dominio)."""
    return urlparse(config.BASE_URL).netloc if config.BASE_URL else ""


def post_fields(post, domain: str | None = None) -> dict:
    """Los textos de la imagen de un post, en su idioma."""
    t = STRINGS[post.lang]
    meta = " · ".join((
        t["author"],
        format_date(post.published_at, post.lang),
        t["minutes"].format(n=post.reading_minutes),
    ))
    return {
        "kind": "post",
        "title": unicodedata.normalize("NFC", post.title),
        "topic": topic_name(post.category, post.lang),
        "meta": meta,
        "domain": site_domain() if domain is None else domain,
        "mark": t["brand_mark"],
        "sub": t["brand_sub"],
    }


def default_fields(lang: str) -> dict:
    t = STRINGS[lang]
    return {"kind": "default", "phrase": t["site_description"], "mark": t["brand_mark"], "sub": t["brand_sub"]}


def fingerprint(fields: dict) -> str:
    payload = json.dumps({"render": RENDER_VERSION, **fields}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()[:_VERSION_LENGTH]


def render(fields: dict) -> Image.Image:
    kind, args = fields["kind"], {k: v for k, v in fields.items() if k != "kind"}
    return draw.post_card(**args) if kind == "post" else draw.default_card(**args)


# ── Archivos ─────────────────────────────────────────────────────────────

def post_image_path(slug: str) -> Path:
    return OG_DIR / f"{slug}.png"


def default_image_path(lang: str) -> Path:
    return OG_DIR / "default" / f"{lang}.png"


def static_path(path: Path) -> str:
    """Ruta bajo /static/ («og/slug.png») de un archivo de OG_DIR."""
    return "og/" + path.relative_to(OG_DIR).as_posix()


def stored_fingerprint(path: Path) -> str | None:
    """La huella guardada en el PNG, o None si no existe o no se puede leer. No decodifica los píxeles."""
    try:
        with Image.open(path) as image:
            return image.info.get(_FINGERPRINT_KEY)
    except (OSError, SyntaxError, ValueError):
        return None


def _write(image: Image.Image, path: Path, print_: str) -> None:
    """Escribe el PNG con su huella, de forma atómica: el servidor nunca sirve uno a medio escribir."""
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngImagePlugin.PngInfo()
    info.add_text(_FINGERPRINT_KEY, print_)
    handle, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as output:
            image.save(output, format="PNG", pnginfo=info, optimize=True)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def ensure(path: Path, fields: dict, force: bool = False) -> bool:
    """Genera la imagen si falta o si su huella no coincide. Devuelve True si la escribió."""
    expected = fingerprint(fields)
    if not force and stored_fingerprint(path) == expected:
        return False
    _write(render(fields), path, expected)
    return True


def remove_post_image(slug: str) -> bool:
    try:
        post_image_path(slug).unlink()
        return True
    except FileNotFoundError:
        return False


# ── Pasada completa (sync, og-images, seed-dev) ──────────────────────────

@dataclass
class ImageReport:
    generated: int = 0
    unchanged: int = 0
    removed: int = 0
    defaults: int = 0                     # imágenes por defecto escritas
    # [(título, slug, error)]: el post queda con la imagen por defecto
    failed: list[tuple[str, str, str]] = field(default_factory=list)


def refresh_images(posts, removed_slugs=(), force: bool = False, prune: bool = False) -> ImageReport:
    """
    Pone al día las imágenes:

    1. borra las de `removed_slugs` (posts borrados o que cambiaron de slug);
    2. con `prune`, borra también cualquier PNG de post que no corresponda a
       ningún post de `posts` (restos de una pasada anterior);
    3. genera las por defecto que falten o hayan cambiado;
    4. genera la de cada post que falte o haya cambiado (todas con `force`).

    Un fallo no corta la pasada: se informa y, si había una imagen vieja, se
    borra, para que el post use la por defecto y no una desactualizada.
    """
    report = ImageReport()
    posts = list(posts)

    for slug in removed_slugs:
        report.removed += remove_post_image(slug)
    if prune and OG_DIR.is_dir():
        keep = {post.slug for post in posts}
        for path in OG_DIR.glob("*.png"):
            if path.stem not in keep:
                path.unlink(missing_ok=True)
                report.removed += 1

    for lang in LANGS:
        try:
            report.defaults += ensure(default_image_path(lang), default_fields(lang), force)
        except Exception as exc:  # noqa: BLE001 — se informa y la pasada sigue
            logger.exception("Imagen por defecto (%s): no se pudo generar", lang)
            report.failed.append((f"default/{lang}", lang, str(exc)))

    domain = site_domain()
    for post in posts:
        try:
            if ensure(post_image_path(post.slug), post_fields(post, domain), force):
                report.generated += 1
            else:
                report.unchanged += 1
        except Exception as exc:  # noqa: BLE001
            logger.exception("Post %r: no se pudo generar su imagen", post.title)
            remove_post_image(post.slug)
            report.failed.append((post.title, post.slug, str(exc)))
    return report


# ── Versión para la URL ──────────────────────────────────────────────────

_versions: dict[Path, tuple[int, int, str | None]] = {}


def image_version(path: Path) -> str | None:
    """
    Huella del PNG en disco, para el `?v=` de la URL; None si no existe. Se
    guarda en memoria por fecha y tamaño del archivo: cada página hace un
    `stat` y lee el PNG solo cuando cambió.
    """
    try:
        stat = path.stat()
    except OSError:
        _versions.pop(path, None)
        return None
    cached = _versions.get(path)
    if cached and cached[:2] == (stat.st_mtime_ns, stat.st_size):
        return cached[2]
    version = stored_fingerprint(path)
    _versions[path] = (stat.st_mtime_ns, stat.st_size, version)
    return version
