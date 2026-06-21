from slugify import slugify

from datetime import datetime

from sqlalchemy import delete

from notion.client import get_posts, get_page_blocks, get_details_from_post
from notion.converter import blocks_to_markdown

from app.render import convert_markdown_to_html

from app.models.category import Category
from app.models.post import Post
from app.models.sync_error import SyncError

from .exceptions import CategoriaFaltanteError


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
    post.published_at = full_post["published_at"]
    post.synced_at = full_post["synced_at"]
    post.category = full_post["category"]

    return post


def _get_full_post(db, post_details, db_categories) -> dict:
    """
    Funcion helper para orquestar: 
    1. El fetch al contenido del post y su transformacion a markdown,
    2. La obtencion o creacion de la categoria asociada al post
    3. Se incorporan las dos nuevas propiedades al diccionario `post_details`
    """
    # OBTENIENDO EL CONTENT
    page_id = post_details["notion_id"]
    page_blocks = get_page_blocks(page_id)
    content_markdown = blocks_to_markdown(page_blocks)
    content_html = convert_markdown_to_html(content_markdown)

    # OBTENIENDO LA CATEGORIA
    category = _get_or_create_category(post_details["category_name"], db, db_categories)

    post_details["content_markdown"] = content_markdown
    post_details["content_html"] = content_html
    post_details["category"] = category
    return post_details


def sync_posts(db):
    """
    Funcion orquestadora
    """
    db_posts = {post.notion_id: post for post in db.query(Post).all()}
    db_categories = {category.name: category for category in db.query(Category).all()}

    notion_posts = get_posts()
    seen_ids = set()

    for notion_post in notion_posts:
        post_details = get_details_from_post(notion_post)
        notion_id = post_details["notion_id"]

        # CATCH de error en el caso de que este venga vacio.
        try:
            if post_details["category_name"] is None:
                raise CategoriaFaltanteError(f"Post {notion_id} no tiene categoria asignada")

            # Esta linea se ejecuta dentro del try/except por logica de negocio.
            # Cualquier post existente que se actualice sin categoria va a ser eliminado de la pagina.
            # Y, es mediante esta linea que se evita o se permite que el post se elimine de los de db.
            seen_ids.add(notion_id)

        except CategoriaFaltanteError as e:
            db.add(SyncError(notion_id=notion_id, message=str(e)))
            db.commit()
            continue

        if notion_id not in db_posts:
            full_post = _get_full_post(db, post_details, db_categories)
            _create_post(db, full_post)

        elif post_details["synced_at"] > db_posts[notion_id].synced_at:
            full_post = _get_full_post(db, post_details, db_categories)
            _update_post(db_posts[notion_id], full_post)
    
    # Cruce de conjuntos para obtener los posts que ya no existen en Notion (Notion es la fuente de verdad)
    to_delete = set(db_posts.keys()) - seen_ids

    stmt = delete(Post).where(Post.notion_id.in_(to_delete))
    db.execute(stmt)
    db.commit()
