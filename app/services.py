from .models.post import Post
from .render import convert_markdown_to_html

def backfill_html(db):
    """
    funcion one-time only
    Esta encargada de derivar content_markdown -> content_html
    """
    db_posts = db.query(Post).all()

    for post in db_posts:
        content_html = convert_markdown_to_html(post.content_markdown)
        post.content_html = content_html
    
    db.commit()
    
