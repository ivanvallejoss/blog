from sqlalchemy import and_, func, or_
from sqlalchemy.orm import joinedload, selectinload

from app.i18n import topic_name
from app.models.post import Post
from app.models.category import Category

# Todo selector que lista o cuenta posts recibe el idioma: un post tiene uno
# solo y aparece únicamente en las páginas de ese idioma.


def get_published_posts(db, lang):
    """
    Posts de un idioma, el destacado primero y después por publicación.
    Se hace un join de Category para poblar `post.category` por cada post.
    """
    posts = db.query(
        Post
        ).options(
            joinedload(Post.category)
            ).filter(
                Post.lang == lang
            ).order_by(
                    Post.featured.desc(),
                    Post.published_at.desc()
                ).all()
    
    return posts


def get_recent_posts(db, lang, limit=None):
    """
    Posts de un idioma del más nuevo al más viejo, sin adelantar el destacado
    (índice de búsqueda, «Quizás buscabas» de la 404). Con `limit`, solo los
    primeros.
    """
    query = (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(Post.lang == lang)
        .order_by(Post.published_at.desc(), Post.id.desc())
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def get_category_by_slug(db, slug):
    "Obtiene el objeto category y los posts relacionadas a este."
    category = db.query(
        Category
        ).options(
            selectinload(Category.posts)
            ).filter_by(
                slug=slug
                ).one_or_none()

    return category


def get_post_by_slugs(db, category_slug, post_slug, lang):
    """
    Obtiene el post mediante su slug, 
    tambien filtra con category_slug para poblar post.category.
    Solo si el post es de `lang`: bajo las rutas del otro idioma no existe.
    """
    post = db.query(
        Post
        ).join(
        Category
    ).options(
        joinedload(Post.category)
        ).filter(
            Category.slug == category_slug, Post.slug == post_slug, Post.lang == lang
        ).one_or_none()

    return post


def get_tag_counts(db, lang):
    """
    Temas con su cantidad de posts en `lang`, de más a menos posts y por
    nombre visible en ese idioma:
    [{"name": "concurrencia", "slug": "concurrencia", "count": 3}, ...]
    `name` es el de Notion; el template muestra `topic_name` (filtro `topic`).
    Solo temas con al menos un post en el idioma. El «Todo» de los filtros no
    sale de acá: lo arma el template con el texto del diccionario y el total.
    """
    rows = (
        db.query(Category.name, Category.slug, func.count(Post.id))
        .join(Post, Post.category_id == Category.id)
        .filter(Post.lang == lang)
        .group_by(Category.id)
        .all()
    )
    tags = [{"name": name, "slug": slug, "count": count} for name, slug, count in rows]
    return sorted(tags, key=lambda tag: (-tag["count"], topic_name(tag, lang).lower()))


def count_posts(db, lang, category_id=None):
    """Cantidad de posts en `lang`, en total o de un tema (estado vacío por idioma)."""
    query = db.query(func.count(Post.id)).filter(Post.lang == lang)
    if category_id is not None:
        query = query.filter(Post.category_id == category_id)
    return query.scalar()


def get_posts_by_year(db, lang, category_id=None):
    """
    Posts del archivo en `lang`, agrupados por año, del más nuevo al más viejo:
    [{"year": 2026, "posts": [Post, ...]}, ...]
    Con `category_id`, solo los de ese tema. Dentro de cada año, por fecha
    descendente: en el archivo el destacado no se adelanta.
    """
    query = db.query(Post).options(joinedload(Post.category)).filter(Post.lang == lang)
    if category_id is not None:
        query = query.filter(Post.category_id == category_id)
    posts = query.order_by(Post.published_at.desc()).all()

    groups = []
    for post in posts:
        year = post.published_at.year
        if not groups or groups[-1]["year"] != year:
            groups.append({"year": year, "posts": []})
        groups[-1]["posts"].append(post)
    return groups


def group_posts_by_tag(posts, tags):
    """
    Bloques por tema de la portada: cada tema de `tags` (en ese orden) con sus
    posts de `posts` (en el orden recibido). No consulta la base: reusa la
    lista que la portada ya trajo.
    """
    by_slug = {}
    for post in posts:
        by_slug.setdefault(post.category.slug, []).append(post)
    return [{**tag, "posts": by_slug.get(tag["slug"], [])} for tag in tags]


def get_next_post(db, post):
    """
    «Siguiente» al pie del artículo: el post publicado inmediatamente antes
    que `post` (se lee del más nuevo al más viejo, como el archivo). Con la
    misma fecha desempata el id, para que el orden sea total. Solo entre los
    posts del mismo idioma. None si `post` es el más viejo.
    """
    return (
        db.query(Post)
        .options(joinedload(Post.category))
        .filter(
            Post.lang == post.lang,
            or_(
                Post.published_at < post.published_at,
                and_(Post.published_at == post.published_at, Post.id < post.id),
            )
        )
        .order_by(Post.published_at.desc(), Post.id.desc())
        .first()
    )
