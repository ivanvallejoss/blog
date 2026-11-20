from notion_client import Client
from notion_client.helpers import collect_paginated_api
import os
import re
from datetime import datetime
from dotenv import load_dotenv

from app.i18n import DEFAULT_LANG, LANGS

from .converter import CHILD_TYPES

load_dotenv()

notion = Client(auth=os.environ.get("NOTION_TOKEN"))
DATA_SOURCE_ID = os.environ.get("NOTION_DATA_SOURCE_ID")


def get_posts(filtro="Published"):
    """
    Funcion que devuelve los posts existentes en Notion.
    Es posible filtrar de forma personalizada, no filtrar o filtrar por default.
    """
    params = {"data_source_id": DATA_SOURCE_ID}

    if filtro is not None:
        params["filter"] = {
            "property": "Estado",
            "status": {"equals": filtro}
        }

    # Notion devuelve como máximo 100 resultados por pedido: se sigue el cursor.
    return collect_paginated_api(notion.data_sources.query, **params)


def get_page_blocks(page_id):
    """
    Bloques de una página (o de un bloque) de Notion, con sus hijos.

    Notion devuelve como máximo 100 bloques por pedido: se sigue el cursor
    hasta el final. Los bloques con `has_children` de un tipo que el conversor
    sabe anidar (listas, citas…, ver `CHILD_TYPES`) traen sus hijos en la
    clave `children`, pedidos de la misma forma. Los de tipos no soportados no
    se recorren: no se van a convertir.

    Solo lectura: no escribe nada en Notion.
    """
    blocks = collect_paginated_api(notion.blocks.children.list, block_id=page_id)
    for block in blocks:
        if block.get("has_children") and block.get("type") in CHILD_TYPES:
            block["children"] = get_page_blocks(block["id"])
    return blocks


# Propiedades opcionales de la base de Notion. Pueden no existir todavía, o
# venir vacías en un post: el sync no falla por eso.
LANG_PROPERTY = "Idioma"      # Select con las opciones «es» y «en»
EXCERPT_PROPERTY = "Resumen"  # Texto: la bajada escrita a mano


def _select_name(properties, name):
    """Nombre de la opción elegida en un Select, o None si falta o está vacío."""
    prop = properties.get(name)
    if not prop or prop.get("type") != "select" or not prop.get("select"):
        return None
    return (prop["select"].get("name") or "").strip() or None


def _rich_text(properties, name):
    """Texto plano de una propiedad de texto, o None si falta o está vacía."""
    prop = properties.get(name)
    if not prop or prop.get("type") != "rich_text":
        return None
    value = "".join(rt.get("plain_text", "") for rt in prop.get("rich_text") or []).strip()
    return value or None


def read_lang(properties):
    """
    (lang, desconocido): el idioma del post según `Idioma`. Sin la propiedad o
    vacía, español. Un valor que no es «es» ni «en» también cae a español, y se
    devuelve en `desconocido` para que el sync lo informe.
    """
    value = _select_name(properties, LANG_PROPERTY)
    if value is None:
        return DEFAULT_LANG, None
    code = value.lower()
    if code in LANGS:
        return code, None
    return DEFAULT_LANG, value


# Propiedades obligatorias de la base de Notion, con su tipo. Si a un post le
# falta el valor de una, el sync lo saltea y lo informa (`read_required`); si
# la base no tiene la propiedad, el sync no arranca (`schema_problems`).
REQUIRED_PROPERTIES = {
    "Titulo": "title",
    "slug": "rich_text",
    "Fecha Publicacion": "date",
    "categoria": "select",
}
_TYPE_NAMES = {"title": "Título", "rich_text": "Texto", "date": "Fecha", "select": "Selección"}


def schema_problems(notion_posts) -> list[str]:
    """
    Propiedades obligatorias que la base de Notion no tiene, o que tienen otro
    tipo. Notion trae todas las propiedades de la base en cada página (vacías
    o no), así que una que no aparece en ninguna página no existe en la base.
    Sin posts no hay nada que revisar.
    """
    pages = [page.get("properties") or {} for page in notion_posts]
    if not pages:
        return []
    problems = []
    for name, kind in REQUIRED_PROPERTIES.items():
        present = [props[name] for props in pages if name in props]
        expected = _TYPE_NAMES[kind]
        if not present:
            problems.append(f"La base de Notion no tiene la propiedad «{name}» (tipo {expected}). Creala con ese nombre exacto.")
        elif all(prop.get("type") != kind for prop in present):
            actual = _TYPE_NAMES.get(present[0].get("type"), present[0].get("type"))
            problems.append(f"La propiedad «{name}» de Notion es de tipo {actual}; tiene que ser de tipo {expected}.")
    return problems


# Largo máximo del título y del slug: las columnas `Post.title` y `Post.slug`
# son String(100). Uno más largo hace fallar el INSERT y deshace el sync
# entero, así que el post se saltea antes (tests/test_notion.py comprueba que
# coincide con el modelo).
TEXT_MAX = 100

# Caracteres que puede tener un slug: letras sin tilde, números, guion y guion
# bajo. Todo lo demás (espacios, «/», «?», «#», «%», tildes, «ñ»…) rompe la
# URL del post, la parte en dos o se codifica distinto según quién la arme.
SLUG_CHARS = re.compile(r"[A-Za-z0-9_-]")


def slug_problems(slug: str) -> list[str]:
    """Lo que impide usar `slug` en la URL de un post, en palabras para Notion."""
    problems = []
    if len(slug) > TEXT_MAX:
        problems.append(f"el slug tiene {len(slug)} caracteres y el máximo es {TEXT_MAX} (propiedad «slug»)")
    bad = list(dict.fromkeys(ch for ch in slug if not SLUG_CHARS.fullmatch(ch)))
    if bad:
        shown = ", ".join("espacios" if ch.isspace() else f"«{ch}»" for ch in bad)
        problems.append(
            f"el slug «{slug}» tiene caracteres que no sirven en una URL ({shown}); "
            "usá solo letras sin tilde, números, guion y guion bajo (propiedad «slug»)"
        )
    return problems


def _plain(prop, kind) -> str:
    """Texto plano de una propiedad de título o de texto, sin espacios en los bordes."""
    if not prop or prop.get("type") != kind:
        return ""
    return "".join(rt.get("plain_text", "") for rt in prop.get(kind) or []).strip()


def read_required(properties):
    """
    (valores, problemas) de las propiedades obligatorias de un post.
    `valores` tiene title, slug, published_at y category_name, con None o ""
    donde falta el dato. `problemas` dice, para cada dato que falta, no se
    puede leer o no entra en el sitio (título o slug de más de TEXT_MAX
    caracteres, slug que no sirve en una URL), qué corregir en Notion. Un
    post con problemas no se publica.
    """
    problems = []

    title = _plain(properties.get("Titulo"), "title")
    if not title:
        problems.append("le falta el título (propiedad «Titulo»)")
    elif len(title) > TEXT_MAX:
        problems.append(f"el título tiene {len(title)} caracteres y el máximo es {TEXT_MAX} (propiedad «Titulo»)")

    slug = _plain(properties.get("slug"), "rich_text")
    if not slug:
        problems.append("le falta el slug (propiedad «slug»)")
    else:
        problems.extend(slug_problems(slug))

    published_at = None
    date_prop = properties.get("Fecha Publicacion") or {}
    start = (date_prop.get("date") or {}).get("start") if date_prop.get("type") == "date" else None
    if not start:
        problems.append("le falta la fecha de publicación (propiedad «Fecha Publicacion»)")
    else:
        try:
            published_at = datetime.fromisoformat(start).replace(tzinfo=None)
        except (TypeError, ValueError):
            problems.append(f"la fecha de publicación «{start}» no se puede leer (propiedad «Fecha Publicacion»)")

    category = _select_name(properties, "categoria")
    if category is None:
        problems.append("le falta el tema (propiedad «categoria»)")

    values = {"title": title, "slug": slug, "published_at": published_at, "category_name": category}
    return values, problems


def get_details_from_post(notion_post):
    """
    Metadata de un post de la base de Notion.

    Devuelve un dict con:
        'notion_id': id de la página,
        'title', 'slug', 'published_at', 'category_name': las propiedades
            obligatorias (vacías o None si faltan; ver `problems`),
        'problems': lo que le falta al post para publicarse, en palabras
            que dicen qué corregir en Notion. Vacía si está bien cargado,
        'synced_at': last_edited_time,
        'created_time': creación de la página en Notion (ISO), para elegir
            con un criterio estable entre dos posts con el mismo slug,
        'lang': idioma del post ('es' si falta o es desconocido),
        'lang_unknown': el valor de `Idioma` si no se reconoció, o None,
        'excerpt': la bajada de `Resumen`, o None.
    """
    properties = notion_post["properties"]
    values, problems = read_required(properties)

    post_details = {
        "notion_id": notion_post["id"],
        **values,
        "problems": problems,
        "synced_at": datetime.fromisoformat(notion_post["last_edited_time"]).replace(tzinfo=None),
        "created_time": notion_post.get("created_time") or "",
    }
    post_details["lang"], post_details["lang_unknown"] = read_lang(properties)
    post_details["excerpt"] = _rich_text(properties, EXCERPT_PROPERTY)

    return post_details
