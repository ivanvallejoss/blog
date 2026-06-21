import markdown

md = markdown.Markdown(extensions=['fenced_code', 'codehilite'])

def convert_markdown_to_html(content_markdown: str) -> str:
    """
    Transforma de markdown a html.
    """
    md.reset()

    content_html = md.convert(content_markdown)

    return content_html