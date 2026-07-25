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

def convert_markdown_to_html(content_markdown: str) -> str:
    """
    Transforma de markdown a html.
    """
    md.reset()

    content_html = md.convert(content_markdown)

    return content_html