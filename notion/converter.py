"""
Bloques de Notion → markdown para `app/render.py` (Python-Markdown con
fenced_code, codehilite, toc y sane_lists).

Qué emite:
  heading_1, heading_2  → «## …»  (el H1 de la página es el título del post)
  heading_3             → «### …»
  paragraph             → párrafo
  quote                 → «> …», con sus hijos adentro de la cita
  bulleted_list_item    → «- …»   ┐ ítems consecutivos forman una lista;
  numbered_list_item    → «1. …»  ┘ los hijos van anidados con 4 espacios
  divider               → «---»
  code                  → bloque cercado (o sangrado si está anidado)

Formato en línea: negrita, itálica, tachado, código y links, a partir de las
`annotations` y el `href` de cada fragmento. Se emiten como HTML en línea
(<strong>, <em>, <del>, <code>, <a>) y no como `**`/`*`/`~~`: un marcador de
markdown depende de los espacios y de lo que tiene al lado, y Notion corta los
fragmentos en cualquier lugar («**hola **mundo» no es negrita). Python-Markdown
no trae extensión de tachado, así que <del> es además la única opción sin
dependencias nuevas.

El texto se escapa siempre: los caracteres que markdown interpreta llevan barra
invertida y los que interpreta HTML (<, >, &) van como entidades. Un «*hola*»
o un «<script>» escritos en Notion llegan literales al post.

Todo lo demás (imágenes, callouts, tablas, toggles, embeds…) no se emite y
queda contado en `Conversion.unsupported`, para que el sync lo informe.

El conversor no habla con Notion: recibe los bloques con sus hijos ya
cargados en la clave `children` (ver `notion/client.py · get_page_blocks`).
"""
import html
import re
from collections import Counter
from dataclasses import dataclass, field
from urllib.parse import urlparse

from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

# Tipos cuyos hijos se piden a Notion (has_children). El resto no se convierte,
# así que pedir sus hijos solo gastaría requests.
CHILD_TYPES = frozenset({
    "paragraph",
    "quote",
    "bulleted_list_item",
    "numbered_list_item",
    "heading_1",
    "heading_2",
    "heading_3",
})

_LIST_MARKERS = {"bulleted_list_item": "-", "numbered_list_item": "1."}
_HEADINGS = {"heading_1": "##", "heading_2": "##", "heading_3": "###"}

# Lo que Python-Markdown acepta escapar con barra (Markdown.ESCAPED_CHARS),
# salvo «>», que va como entidad junto con < y &.
_MD_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!])")

# Nombres de lenguaje de Notion que Pygments no reconoce tal cual.
_LANGUAGE_ALIASES = {
    "plain text": "text",
    "visual basic": "vb.net",
    "markup": "html",
    "flow": "javascript",
    "mermaid": "text",
    "webassembly": "wast",
    "java/c/c++/c#": "java",
}
# Lo que fenced_code acepta como lenguaje después de la cerca.
_FENCE_LANG = re.compile(r"^[\w#.+-]+$")

_INDENT = " " * 4  # tab_length de Python-Markdown: anidación de listas y código sangrado
_SAFE_SCHEMES = {"http", "https", "mailto"}
_NOTION_HOSTS = ("notion.so", "notion.site")


@dataclass
class Conversion:
    markdown: str
    # tipo → cantidad. Bloques: el tipo de Notion («image», «callout»…).
    # En línea: «link interno de Notion», «equation (en línea)»…
    unsupported: Counter = field(default_factory=Counter)


def convert_blocks(blocks: list[dict]) -> Conversion:
    """Convierte los bloques de una página. Ver el docstring del módulo."""
    converter = _Converter()
    body = converter.render(blocks, nested=False)
    return Conversion(markdown=f"{body}\n" if body else "", unsupported=converter.unsupported)


def blocks_to_markdown(blocks: list[dict]) -> str:
    """Atajo: solo el markdown."""
    return convert_blocks(blocks).markdown


def code_language(name: str | None) -> str:
    """
    Nombre de lenguaje de Notion → alias de Pygments que entra en una cerca.
    Si Pygments no lo conoce, «text»: el bloque se ve sin colores pero nunca
    se rompe (con «plain text», la cerca dejaba de ser cerca y el código caía
    como texto en línea).
    """
    key = (name or "").strip().lower()
    key = _LANGUAGE_ALIASES.get(key, key)
    if not key:
        return "text"
    try:
        lexer = get_lexer_by_name(key)
    except ClassNotFound:
        return "text"
    alias = lexer.aliases[0] if lexer.aliases else key
    return alias if _FENCE_LANG.match(alias) else "text"


def escape_text(text: str) -> str:
    """Texto literal → markdown que se renderiza igual a ese texto."""
    text = html.escape(text, quote=False)  # & < >
    return _MD_SPECIAL.sub(r"\\\1", text)


class _Converter:
    def __init__(self):
        self.unsupported: Counter = Counter()

    # — bloques —

    def render(self, blocks: list[dict], nested: bool) -> str:
        """
        Markdown de una secuencia de bloques hermanos. Los ítems de lista
        consecutivos del mismo tipo van separados por un salto simple (lista
        compacta); todo lo demás, por una línea en blanco.
        """
        chunks: list[str] = []
        previous_list = None  # tipo del último ítem de lista, si el último bloque fue uno
        previous_item = ""
        for block in blocks:
            kind = block.get("type")
            piece = self.block(block, nested)
            if piece is None:
                previous_list = None
                continue
            if kind in _LIST_MARKERS and kind == previous_list:
                # Si uno de los dos ítems ocupa más de un bloque de markdown
                # (hijos que no son una sublista simple), van separados por una
                # línea en blanco: si no, Python-Markdown toma el ítem nuevo
                # como continuación del último hijo. La lista queda «suelta»
                # (<li><p>…) y la prosa la iguala por CSS.
                loose = "\n\n" in previous_item or "\n\n" in piece
                chunks[-1] += ("\n\n" if loose else "\n") + piece
            else:
                chunks.append(piece)
            previous_list = kind if kind in _LIST_MARKERS else None
            previous_item = piece
        return "\n\n".join(chunks)

    def block(self, block: dict, nested: bool) -> str | None:
        kind = block.get("type")
        data = block.get(kind) or {}
        children = block.get("children") or []

        if kind in _HEADINGS:
            text = self.inline(data.get("rich_text", []))
            parts = [f"{_HEADINGS[kind]} {text}"] if text else []
            # Un título desplegable trae su contenido como hijos: va después.
            if children:
                parts.append(self.render(children, nested))
            return self._join(parts)

        if kind == "paragraph":
            text = self.inline(data.get("rich_text", []))
            parts = [text] if text else []
            # Párrafo con sangría en Notion: sus hijos siguen al mismo nivel.
            if children:
                parts.append(self.render(children, nested))
            return self._join(parts)

        if kind == "quote":
            text = self.inline(data.get("rich_text", []))
            parts = [text] if text else []
            if children:
                parts.append(self.render(children, nested=True))
            inner = self._join(parts)
            if inner is None:
                return None
            return "\n".join(f"> {line}" if line else ">" for line in inner.split("\n"))

        if kind in _LIST_MARKERS:
            text = self.inline(data.get("rich_text", []))
            if not text and not children:
                return None  # viñeta vacía, típica al final de una lista en Notion
            item = f"{_LIST_MARKERS[kind]} {text}"
            if children:
                inner = self.render(children, nested=True)
                if inner:
                    # Una sublista sigue pegada al ítem; cualquier otro bloque
                    # necesita una línea en blanco para no fundirse con su texto.
                    first = children[0].get("type")
                    glue = "\n" if first in _LIST_MARKERS else "\n\n"
                    item += glue + _indent(inner)
            return item

        if kind == "divider":
            return "---"

        if kind == "code":
            return self.code(data, nested)

        self.unsupported[kind or "desconocido"] += 1
        return None

    def code(self, data: dict, nested: bool) -> str:
        source = "".join(rt.get("plain_text", "") for rt in data.get("rich_text", []))
        language = code_language(data.get("language"))
        if nested:
            # fenced_code solo reconoce cercas en la columna 0: adentro de una
            # lista o una cita va como código sangrado, con el lenguaje en la
            # primera línea (sintaxis «:::» de codehilite).
            return _indent(f":::{language}\n{source}")
        longest = max((len(run) for run in re.findall(r"^`{3,}", source, flags=re.M)), default=2)
        fence = "`" * max(3, longest + 1)
        return f"{fence}{language}\n{source}\n{fence}"

    # — en línea —

    def inline(self, rich_text: list[dict]) -> str:
        out = []
        for fragment in _merge(rich_text):
            # Los saltos de línea de Notion (Mayús+Enter) son <br>: así el
            # bloque queda en una sola línea de markdown y no hay sangrías
            # que cuidar adentro de listas ni de citas.
            lines = fragment["text"].split("\n")
            out.append("<br>".join(self.fragment(fragment, line) if line else "" for line in lines))
        return "".join(out).strip()

    def fragment(self, fragment: dict, text: str) -> str:
        # Los espacios de los bordes quedan fuera de las etiquetas: Notion suele
        # incluir el espacio siguiente en la negrita o en el link.
        core = text.strip()
        if not core:
            return escape_text(text)
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()):]
        return f"{lead}{self.wrap(fragment, escape_text(core))}{trail}"

    def wrap(self, fragment: dict, piece: str) -> str:
        if fragment["equation"]:
            self.unsupported["equation (en línea)"] += 1
            piece = f"<code>{piece}</code>"
        if fragment["code"]:
            piece = f"<code>{piece}</code>"
        if fragment["strikethrough"]:
            piece = f"<del>{piece}</del>"
        if fragment["italic"]:
            piece = f"<em>{piece}</em>"
        if fragment["bold"]:
            piece = f"<strong>{piece}</strong>"
        href = self.link(fragment["href"])
        if href:
            piece = f'<a href="{html.escape(href, quote=True)}">{piece}</a>'
        return piece

    def link(self, href: str | None) -> str | None:
        """
        URL del fragmento o None. Los links a páginas de Notion (menciones o
        links internos) no se publican: llevarían al workspace privado. Queda
        el texto y se informa. Esquemas que no sean http(s)/mailto, igual.
        """
        if not href:
            return None
        parsed = urlparse(href)
        if href.startswith("/") or (parsed.hostname or "").endswith(_NOTION_HOSTS):
            self.unsupported["link interno de Notion"] += 1
            return None
        if parsed.scheme.lower() not in _SAFE_SCHEMES:
            self.unsupported[f"link {parsed.scheme or 'sin esquema'}:"] += 1
            return None
        return href

    @staticmethod
    def _join(parts: list[str]) -> str | None:
        parts = [p for p in parts if p]
        return "\n\n".join(parts) if parts else None


def _merge(rich_text: list[dict]) -> list[dict]:
    """
    Normaliza los fragmentos y junta los vecinos con el mismo formato y el
    mismo link: Notion a veces parte una palabra en dos fragmentos iguales, y
    eso daría «<strong>ho</strong><strong>la</strong>».
    """
    merged: list[dict] = []
    for rt in rich_text:
        annotations = rt.get("annotations") or {}
        fragment = {
            "text": rt.get("plain_text", ""),
            "bold": bool(annotations.get("bold")),
            "italic": bool(annotations.get("italic")),
            "strikethrough": bool(annotations.get("strikethrough")),
            "code": bool(annotations.get("code")),
            "equation": rt.get("type") == "equation",
            "href": rt.get("href"),
        }
        if not fragment["text"]:
            continue
        if merged and all(merged[-1][k] == fragment[k] for k in fragment if k != "text"):
            merged[-1]["text"] += fragment["text"]
        else:
            merged.append(fragment)
    return merged


def _indent(text: str) -> str:
    return "\n".join(f"{_INDENT}{line}" if line else "" for line in text.split("\n"))
