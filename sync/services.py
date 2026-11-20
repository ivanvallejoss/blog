import logging
from collections import Counter
from dataclasses import dataclass, field

from slugify import slugify

from sqlalchemy import delete
from sqlalchemy.orm import joinedload

from notion.client import get_posts, get_page_blocks, get_details_from_post, schema_problems
from notion.converter import convert_blocks

from app.og.images import ImageReport, refresh_images
from app.render import render_markdown
from app.urls import RESERVED_TOPIC_SLUGS

from app.models.category import Category
from app.models.post import Post
from app.models.sync_error import SyncError

from .exceptions import EsquemaNotionError

logger = logging.getLogger(__name__)


@dataclass
class SyncReport:
    """
    Resultado de un sync, para que `cli.py` lo muestre.
    `unsupported`: por post reconvertido, lo que el conversor no pudo emitir
    [(título, notion_id, Counter(tipo → cantidad)), ...].
    `unknown_lang`: posts cuyo `Idioma` no es «es» ni «en» y quedaron en
    español [(título, notion_id, valor), ...].
    `reserved_topics`: temas cuyo slug choca con una ruta fija (app/urls.py)
    [(nombre, slug), ...]: sus páginas quedan tapadas en al menos un idioma.
    `images`: la pasada de imágenes para compartir (app/og/images.py), con
    las que fallaron.
    `rejected`: posts publicados en Notion que no se publicaron por un dato
    obligatorio que falta o no entra en el sitio, o porque repiten el slug
    de otro
    [(título, notion_id, [motivos]), ...]. Si ya estaban en la base, se
    borran, como cualquier post que deja de estar publicado.
    """
    created: int = 0
    updated: int = 0
    deleted: int = 0
    skipped: int = 0  # sin cambios en Notion desde el último sync
    unsupported: list[tuple[str, str, Counter]] = field(default_factory=list)
    unknown_lang: list[tuple[str, str, str]] = field(default_factory=list)
    reserved_topics: list[tuple[str, str]] = field(default_factory=list)
    images: ImageReport = field(default_factory=ImageReport)
    rejected: list[tuple[str, str, list[str]]] = field(default_factory=list)


def _get_or_create_category(name, db, db_categories):
    """
    Funcion helper para validar la existencia de una categoria en db.
    En caso de no existir la referencia se crea en db y se la agrega al diccionario.
    La funcion devuelve un objeto Category nuevo o el existente en db.
    """
    if name in db_categories:
        return db_categories[name] 
    
    slug = slugify(name)
    the_category = Category(name=name, slug=slug)
    
    db_categories[the_category.name] = the_category
    db.add(the_category)

    return the_category


def _create_post(db, full_post):
    """
    Funcion helper para crear un post en db.
    Se crea el post en DB como parte de la session.
    """
    new_post = Post(
        title=full_post["title"],
        slug=full_post["slug"],
        content_markdown=full_post["content_markdown"],
        content_html=full_post["content_html"],
        content_toc=full_post["content_toc"],
        lang=full_post["lang"],
        excerpt=full_post["excerpt"],
        published_at=full_post["published_at"],
        notion_id=full_post["notion_id"],
        synced_at=full_post["synced_at"],
    )
    new_post.category = full_post["category"]
    db.add(new_post)

    return new_post



def _update_post(post, full_post):
    """
    Funcion helper para actualizar un post existente en db con los datos nuevos de Notion.
    """
    post.title = full_post["title"]
    post.slug = full_post["slug"]
    post.content_markdown = full_post["content_markdown"]
    post.content_html = full_post["content_html"]
    post.content_toc = full_post["content_toc"]
    post.lang = full_post["lang"]
    post.excerpt = full_post["excerpt"]
    post.published_at = full_post["published_at"]
    post.synced_at = full_post["synced_at"]
    post.category = full_post["category"]

    return post


def _get_full_post(db, post_details, db_categories, report) -> dict:
    """
    Funcion helper para orquestar: 
    1. El fetch al contenido del post y su transformacion a markdown,
    2. La obtencion o creacion de la categoria asociada al post
    3. Se incorporan las nuevas propiedades al diccionario `post_details`
    """
    # OBTENIENDO EL CONTENT
    page_id = post_details["notion_id"]
    page_blocks = get_page_blocks(page_id)
    conversion = convert_blocks(page_blocks)
    content_markdown = conversion.markdown
    # El título de las anclas queda escrito en el HTML: en el idioma del post.
    content_html, content_toc = render_markdown(content_markdown, post_details["lang"])

    # Lo que no se pudo convertir se informa y el sync sigue: el post se
    # publica sin esos bloques.
    if conversion.unsupported:
        report.unsupported.append((post_details["title"], page_id, conversion.unsupported))
        logger.warning(
            "Post %r (%s): tipos no soportados: %s",
            post_details["title"], page_id,
            ", ".join(f"{kind} ×{n}" for kind, n in conversion.unsupported.items()),
        )

    # OBTENIENDO LA CATEGORIA
    category = _get_or_create_category(post_details["category_name"], db, db_categories)

    post_details["content_markdown"] = content_markdown
    post_details["content_html"] = content_html
    post_details["content_toc"] = content_toc
    post_details["category"] = category
    return post_details


def sync_posts(db, force=False) -> SyncReport:
    """
    Funcion orquestadora.

    Un post existente solo se reconvierte si cambió en Notion desde el último
    sync. Con `force`, se reconvierten todos (por ejemplo, después de cambiar
    el conversor).
    """
    report = SyncReport()
    notion_posts = get_posts()

    # Una propiedad obligatoria que la base de Notion no tiene dejaría a
    # todos los posts salteados (y borraría el sitio): el sync no arranca.
    problems = schema_problems(notion_posts)
    if problems:
        raise EsquemaNotionError(problems)

    db_posts = {post.notion_id: post for post in db.query(Post).all()}
    db_categories = {category.name: category for category in db.query(Category).all()}

    seen_ids = set()
    removed_slugs = []  # imágenes para compartir que hay que borrar
    topic_names = set()

    all_details = [get_details_from_post(notion_post) for notion_post in notion_posts]
    for post_details in all_details:
        # Un Idioma desconocido no corta el sync: el post queda en español y
        # se informa. Se informa en cada sync, cambie o no el post, hasta que
        # se corrija en Notion.
        if post_details["lang_unknown"] is not None:
            report.unknown_lang.append((post_details["title"], post_details["notion_id"], post_details["lang_unknown"]))
            logger.warning(
                "Post %r (%s): Idioma desconocido %r, queda en español",
                post_details["title"], post_details["notion_id"], post_details["lang_unknown"],
            )

    # Un post al que le falta un dato obligatorio, cuyo título o slug no
    # entra en el sitio (más de 100 caracteres, slug que no sirve en una URL;
    # ver notion/client.py · read_required), o que repite el slug de otro, no
    # se publica: se saltea, se informa y el sync sigue con los
    # demás. No entra en `seen_ids`, así que si ya estaba en la base se borra
    # (Notion es la fuente de verdad), hasta que se corrija.
    valid = [d for d in all_details if not d["problems"]]
    rejected = [(d, d["problems"]) for d in all_details if d["problems"]]
    valid, duplicated = _drop_duplicate_slugs(valid, db_posts)
    for post_details, reasons in rejected + duplicated:
        report.rejected.append((post_details["title"], post_details["notion_id"], reasons))
        db.add(SyncError(notion_id=post_details["notion_id"], message="; ".join(reasons)))
        logger.warning("Post %r (%s) salteado: %s", post_details["title"],
                       post_details["notion_id"], "; ".join(reasons))
    if report.rejected:
        db.commit()

    for post_details in valid:
        notion_id = post_details["notion_id"]
        seen_ids.add(notion_id)
        topic_names.add(post_details["category_name"])

        if notion_id not in db_posts:
            full_post = _get_full_post(db, post_details, db_categories, report)
            _create_post(db, full_post)
            report.created += 1

        elif force or post_details["synced_at"] > db_posts[notion_id].synced_at:
            full_post = _get_full_post(db, post_details, db_categories, report)
            old_slug = db_posts[notion_id].slug
            _update_post(db_posts[notion_id], full_post)
            if old_slug != full_post["slug"]:
                removed_slugs.append(old_slug)  # su imagen queda huérfana
            report.updated += 1

        else:
            report.skipped += 1

    # Cruce de conjuntos para obtener los posts que ya no existen en Notion (Notion es la fuente de verdad)
    to_delete = set(db_posts.keys()) - seen_ids
    removed_slugs += [db_posts[notion_id].slug for notion_id in to_delete]

    stmt = delete(Post).where(Post.notion_id.in_(to_delete))
    db.execute(stmt)
    db.commit()
    report.deleted = len(to_delete)
    report.images = _refresh_images(db, removed_slugs)
    report.reserved_topics = reserved_topics(topic_names)
    for name, slug in report.reserved_topics:
        logger.warning("Tema %r: el slug %r choca con una ruta fija del sitio", name, slug)
    return report


def _drop_duplicate_slugs(valid, db_posts):
    """
    (conservados, salteados) cuando dos o más posts publicados comparten slug,
    que en la base es único. Se conserva, con un criterio estable:

    1. el que ya estaba publicado con ese slug, para no cambiar su URL;
    2. si no, el que se creó antes en Notion (y, a igual fecha, el de menor id).

    Los demás se saltean, con un motivo que nombra al conservado.
    """
    by_slug = {}
    for post_details in valid:
        by_slug.setdefault(post_details["slug"], []).append(post_details)

    kept, skipped = [], []
    for slug, group in by_slug.items():
        if len(group) == 1:
            kept.append(group[0])
            continue
        owners = [d for d in group if d["notion_id"] in db_posts and db_posts[d["notion_id"]].slug == slug]
        if owners:
            winner, why = owners[0], "ya estaba publicado con ese slug"
        else:
            winner = min(group, key=lambda d: (d["created_time"], d["notion_id"]))
            why = "se creó antes en Notion"
        kept.append(winner)
        for loser in group:
            if loser is not winner:
                skipped.append((loser, [
                    f"tiene el mismo slug «{slug}» que «{winner['title']}» ({winner['notion_id']}), "
                    f"que se conservó porque {why}; cambiá el slug de uno de los dos"
                ]))
    order = {id(d): i for i, d in enumerate(valid)}
    return sorted(kept, key=lambda d: order[id(d)]), skipped


def _refresh_images(db, removed_slugs) -> ImageReport:
    """
    Imágenes para compartir, después de guardar los posts: borra las de los
    posts borrados (o que cambiaron de slug) y genera las que falten o cuyo
    contenido cambió (título, tema, fecha, minutos, dominio). Las que no
    cambiaron no se tocan. Un fallo no corta el sync: queda en el reporte y el
    post usa la imagen por defecto.
    """
    try:
        posts = db.query(Post).options(joinedload(Post.category)).all()
        return refresh_images(posts, removed_slugs)
    except Exception as exc:  # noqa: BLE001 — el sync ya guardó los posts
        logger.exception("Imágenes para compartir: la pasada no terminó")
        return ImageReport(failed=[("(todas)", "", str(exc))])


def reserved_topics(names) -> list[tuple[str, str]]:
    """[(nombre, slug), ...] de los temas cuyo slug choca con una ruta fija."""
    return sorted(
        (name, slugify(name)) for name in names if slugify(name) in RESERVED_TOPIC_SLUGS
    )
