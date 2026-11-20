from .models.post import Post
from .render import render_markdown

def backfill_html(db):
    """
    Re-deriva content_markdown -> (content_html, content_toc) para todos
    los posts. Herramienta recurrente: corre cada vez que cambia el
    renderer o el converter, sin necesidad de re-sincronizar Notion.
    """
    db_posts = db.query(Post).all()

    for post in db_posts:
        post.content_html, post.content_toc = render_markdown(post.content_markdown, post.lang)
    
    db.commit()
    