import typer
from app.database import SessionLocal
from app.services import backfill_html
from sync.services import sync_posts

app = typer.Typer()

@app.command()
def sync():
    """Sincroniza los posts desde Notion."""
    with SessionLocal() as db:
        sync_posts(db)

@app.command()
def feature(slug: str, off: bool = typer.Option(False, "--off", help="Quitar el destacado")):
    """Marca (o desmarca con --off) un post como destacado."""
    from app.models.post import Post
    with SessionLocal() as db:
        post = db.query(Post).filter_by(slug=slug).one_or_none()
        if not post:
            typer.echo(f"No existe post con slug '{slug}'")
            raise typer.Exit(code=1)
        post.featured = not off
        db.commit()
        typer.echo(f"'{post.title}' -> featured={post.featured}")

@app.command()
def backfill_db():
    """Deriva content_markdown -> content_html """
    with SessionLocal() as db:
        backfill_html(db)


if __name__ == "__main__":
    app()