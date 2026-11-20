import html

import markdown
from markupsafe import Markup
from slugify import slugify as _slugify

# sane_lists: una lista con viñetas seguida de una numerada son dos listas, no
# una sola (sin esto Python-Markdown las funde). Las listas anidadas no
# necesitan extensión: 4 espacios de sangría. El tachado tampoco: el conversor
# emite <del> en línea (Python-Markdown no trae extensión de tachado).
md = markdown.Markdown(
    extensions=['fenced_code', 'codehilite', 'toc', 'sane_lists'],
    extension_configs={
        'toc': {
            'slugify': lambda value, separator: _slugify(value, separator=separator),
            'permalink': '#',
            'permalink_title': 'Enlace a esta sección',
        }
    },
)


def _flatten_toc(tokens: list[dict]) -> list[dict]:
    """
    Aplana el árbol de md.toc_tokens a una lista lineal.
    El bloque «En este artículo» lista h2 y h3 en una sola columna, sin
    jerarquía visual, así que la anidación no aporta nada acá.
    """
    flat = []
    for token in tokens:
        flat.append({
            "level": token["level"],
            "id": token["id"],
            # toc_tokens trae el nombre escapado como HTML («&amp;»); se guarda
            # como texto plano y el template lo escapa una sola vez.
            "text": html.unescape(token["name"]),
        })
        flat.extend(_flatten_toc(token["children"]))
    return flat


def render_markdown(content_markdown: str) -> tuple[str, list[dict]]:
    """
    Deriva content_markdown -> (content_html, content_toc).

    Único punto del sistema que lee md.toc_tokens: los ids de «En este artículo» son
    literalmente los que el renderer puso en los headings, no una lista
    paralela mantenida a mano.
    """
    md.reset()

    content_html = md.convert(content_markdown)
    content_toc = _flatten_toc(md.toc_tokens)

    return content_html, content_toc

# Instancia aparte, sin extensiones: solo pasa un fragmento a texto plano.
_plain = markdown.Markdown()


def markdown_to_text(source: str) -> str:
    """
    Markdown de un párrafo → texto plano, sin etiquetas ni escapes
    («<strong>Hola</strong> \\*x\\* &amp;» → «Hola *x* &»). Para la bajada
    derivada (Post.summary), que se muestra como texto.
    """
    _plain.reset()
    return Markup(_plain.convert(source)).striptags()
