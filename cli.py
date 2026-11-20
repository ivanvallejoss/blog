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
    Un post publicado al que le falta un dato obligatorio (título, slug,
    Fecha Publicacion, categoria), con un título o un slug de más de 100
    caracteres, con un slug que no sirve en una URL, o que repite el slug de
    otro, se saltea y se lista al final con el motivo; los demás se
    sincronizan igual. Si a la
    base de Notion le falta una de esas propiedades, no se cambia nada.
    Al final informa también los tipos de bloque que el conversor no soporta,
    por post, los valores de Idioma que no reconoce y los temas cuyo slug
    choca con una ruta fija del sitio.
    """
    from sync.exceptions import EsquemaNotionError

    with SessionLocal() as db:
        try:
            report = sync_posts(db, force=force)
        except EsquemaNotionError as exc:
            typer.echo("El sync no se hizo: a la base de Notion le falta algo obligatorio. No se cambió nada.")
            for problem in exc.problems:
                typer.echo(f"  {problem}")
            raise typer.Exit(code=1)
    typer.echo(
        f"Sync: {report.created} nuevos, {report.updated} reconvertidos, "
        f"{report.skipped} sin cambios, {report.deleted} borrados, {len(report.rejected)} salteados."
    )
    if report.rejected:
        typer.echo("Salteados (no se publicaron; si ya estaban en el sitio, se quitaron hasta que se corrijan en Notion):")
    for title, notion_id, reasons in report.rejected:
        name = f"«{title}» ({notion_id})" if title else f"Post sin título ({notion_id})"
        typer.echo(f"  {name}: {'; '.join(reasons)}.")
    for title, notion_id, kinds in report.unsupported:
        detail = ", ".join(f"{kind} ×{n}" for kind, n in sorted(kinds.items()))
        typer.echo(f"  No soportado en «{title}» ({notion_id}): {detail}")
    for title, notion_id, value in report.unknown_lang:
        typer.echo(f"  Idioma desconocido en «{title}» ({notion_id}): «{value}». Quedó en español; los valores válidos son «es» y «en».")
    for name, slug in report.reserved_topics:
        typer.echo(f"  El tema «{name}» tiene el slug «{slug}», que choca con una ruta fija del sitio: renombralo en Notion.")
    _echo_images(report.images)


def _echo_images(report) -> None:
    """Resumen de una pasada de imágenes para compartir (app/og/images.py)."""
    typer.echo(
        f"Imágenes: {report.generated} generadas, {report.unchanged} sin cambios, "
        f"{report.removed} borradas, {report.defaults} por defecto escritas."
    )
    for title, slug, error in report.failed:
        typer.echo(f"  No se pudo generar la imagen de «{title}» ({slug}): {error}. Usa la imagen por defecto.")


def _warn_images() -> None:
    """Avisos de entorno que cambian lo que se dibuja."""
    from app.og.draw import RAQM
    from app.og.images import site_domain
    if not site_domain():
        typer.echo("Aviso: BLOG_BASE_URL no está definida; las imágenes de post salen sin dominio.")
    if not RAQM:
        typer.echo("Aviso: Pillow no tiene libraqm (falta libfribidi en el sistema); el texto sale sin kerning.")

@app.command("og-images")
def og_images(
    force: bool = typer.Option(False, "--force", help="Regenerar todas, aunque no hayan cambiado."),
):
    """
    Genera las imágenes para compartir (OpenGraph) en static/og/.

    Escribe las dos por defecto (una por idioma) y la de cada post, solo las
    que faltan o cuyo contenido cambió; con --force, todas. Borra las de
    posts que ya no existen. El sync hace lo mismo para los posts que toca;
    este comando sirve al desplegar y después de cambiar el dibujo.
    Sale con código 1 si alguna falló (el post usa la por defecto).
    """
    from sqlalchemy.orm import joinedload
    from app.models.post import Post
    from app.og.images import refresh_images

    _warn_images()
    with SessionLocal() as db:
        posts = db.query(Post).options(joinedload(Post.category)).all()
        report = refresh_images(posts, force=force, prune=True)
    _echo_images(report)
    if report.failed:
        raise typer.Exit(code=1)

@app.command("touch-icon")
def touch_icon():
    """
    Dibuja static/public/apple-touch-icon.png (180 × 180) con el mismo código
    del anillo que las imágenes para compartir. El archivo se commitea: este
    comando solo hace falta si cambia el anillo o sus tokens.
    """
    from app.og.draw import touch_icon as draw_touch_icon
    path = "static/public/apple-touch-icon.png"
    draw_touch_icon().save(path, format="PNG", optimize=True)
    typer.echo(f"Escrito {path}.")

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
    Carga los posts de muestra del diseño (solo desarrollo local).

    Inserta o actualiza los posts del prototipo Broadsheet con notion_id
    "seed-…": los siete en español y cinco de ellos en inglés, con su bajada
    en `excerpt`. Tres temas, dos años y un destacado por idioma; «life»
    queda solo en español y «herramientas» sin posts, para los estados
    vacíos.

    Necesita las dos cosas: BLOG_ALLOW_SEED=1 en el entorno y DATABASE_URL
    apuntando a localhost o 127.0.0.1. En el servidor no se define
    BLOG_ALLOW_SEED, así que se niega aunque la base sea local.
    Ejemplo: BLOG_ALLOW_SEED=1 uv run python cli.py seed-dev

    Genera también sus imágenes para compartir (y --clear las borra).

    Ojo: `sync` borra estos posts, porque Notion es la fuente de verdad y
    allá no existen. Es el comportamiento esperado: después de un sync,
    volver a correr seed-dev.
    """
    import os
    from app.config import SEED_ALLOWED
    from app.seed import clear_seed_posts, is_local_database, seed_posts

    if not SEED_ALLOWED:
        typer.echo("seed-dev está deshabilitado: es solo para desarrollo local. Para habilitarlo, definí BLOG_ALLOW_SEED=1 (nunca en el servidor).")
        raise typer.Exit(code=1)
    if not is_local_database(os.environ.get("DATABASE_URL")):
        typer.echo("seed-dev solo corre contra una base local (localhost o 127.0.0.1). Revisá DATABASE_URL.")
        raise typer.Exit(code=1)

    from app.og.images import refresh_images

    with SessionLocal() as db:
        if clear:
            posts, categories, slugs = clear_seed_posts(db)
            typer.echo(f"Borrados {posts} posts seed y {categories} temas vacíos.")
            _echo_images(refresh_images([], removed_slugs=slugs))
            return
        posts = seed_posts(db)
        for post in posts:
            prefix = "en/" if post.lang == "en" else ""
            typer.echo(f"{post.published_at:%Y-%m-%d}  {prefix}{post.category.slug}/{post.slug}  ({post.reading_minutes} min)")
        typer.echo(f"{len(posts)} posts de muestra cargados.")
        # Con imagen para compartir, como los del sync.
        _warn_images()
        _echo_images(refresh_images(posts))

@app.command()
def backfill_db():
    """Deriva content_markdown -> content_html """
    with SessionLocal() as db:
        backfill_html(db)


if __name__ == "__main__":
    app()