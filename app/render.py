import markdown
from slugify import slugify as _slugify

md = markdown.Markdown(
    extensions=['fenced_code', 'codehilite', 'toc'],
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
            "text": token["name"],
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