import typer
from app.database import SessionLocal
from app.services import backfill_html
from sync.services import sync_posts

app = typer.Typer()

@app.command()
def sync(
    force: bool = typer.Option(False, "--force", help="Reconvertir todos los posts, aunque no hayan cambiado en Notion."),
):
    """
    Sincroniza los posts desde Notion (solo lectura del lado de Notion).

    Un post solo se reconvierte si cambió en Notion; con --force se
    reconvierten todos, por ejemplo después de cambiar el conversor.
    Al final informa los tipos de bloque que el conversor no soporta, por post.
    """
    with SessionLocal() as db:
        report = sync_posts(db, force=force)
    typer.echo(
        f"Sync: {report.created} nuevos, {report.updated} reconvertidos, "
        f"{report.skipped} sin cambios, {report.deleted} borrados."
    )
    for title, notion_id, kinds in report.unsupported:
        detail = ", ".join(f"{kind} ×{n}" for kind, n in sorted(kinds.items()))
        typer.echo(f"  No soportado en «{title}» ({notion_id}): {detail}")

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

@app.command("seed-dev")
def seed_dev(
    clear: bool = typer.Option(False, "--clear", help="Borrar los posts seed-… y los temas que queden vacíos, sin volver a cargarlos."),
):
    """
    Carga los siete posts de muestra del diseño (solo desarrollo local).

    Inserta o actualiza los posts del prototipo Broadsheet con notion_id
    "seed-…": tres temas, dos años, uno destacado, y un tema sin posts
    («herramientas») para el estado vacío. Se niega a correr si
    DATABASE_URL no apunta a localhost o 127.0.0.1.

    Ojo: `sync` borra estos posts, porque Notion es la fuente de verdad y
    allá no existen. Es el comportamiento esperado: después de un sync,
    volver a correr seed-dev.
    """
    import os
    from app.seed import clear_seed_posts, is_local_database, seed_posts

    if not is_local_database(os.environ.get("DATABASE_URL")):
        typer.echo("seed-dev solo corre contra una base local (localhost o 127.0.0.1). Revisá DATABASE_URL.")
        raise typer.Exit(code=1)

    with SessionLocal() as db:
        if clear:
            posts, categories = clear_seed_posts(db)
            typer.echo(f"Borrados {posts} posts seed y {categories} temas vacíos.")
            return
        posts = seed_posts(db)
        for post in posts:
            typer.echo(f"{post.published_at:%Y-%m-%d}  {post.category.slug}/{post.slug}  ({post.reading_minutes} min)")
        typer.echo(f"{len(posts)} posts de muestra cargados.")

@app.command()
def backfill_db():
    """Deriva content_markdown -> content_html """
    with SessionLocal() as db:
        backfill_html(db)


if __name__ == "__main__":
    app()