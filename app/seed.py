"""
Datos de prueba para desarrollo local: los siete posts del prototipo
(`docs/design_handoff_blog_broadsheet/design/Blog 1a.dc.html`, arreglo `raw`).

Mismos títulos, bajadas, fechas y temas que el diseño, para que portada,
archivo y artículo se comparen directo contra él. El cuerpo es markdown con
varios h2, párrafos y un bloque de código, pasado por `render_markdown` igual
que en el sync. Los minutos de lectura se aproximan a los del diseño
completando cada post con párrafos de relleno.

El destacado no se escribe en markdown: es una lista de bloques de Notion
hechos a mano (`FEATURED_BLOCKS`) que pasa por `notion/converter.py`, así la
página muestra exactamente lo que el sync emitiría. Sigue la muestra de prosa
del diseño (`PostBody.dc.html`) y suma lo que el conversor sabe hacer: cita,
las dos listas, una anidada, formato en línea, un link y texto que se escapa.

Además deja un tema sin posts (`EMPTY_TOPICS`) para probar el estado vacío:
no aparece como filtro, pero su URL responde.

Todos llevan `notion_id` con prefijo `seed-`: así se reconocen y se borran
sin tocar lo que vino de Notion. `sync` también los borra, porque Notion es la
fuente de verdad y estos posts no existen allá.
"""
from datetime import datetime
from itertools import cycle

from slugify import slugify
from sqlalchemy.engine import make_url

from app.models.category import Category
from app.models.post import Post
from app.render import render_markdown
from notion.converter import blocks_to_markdown

SEED_PREFIX = "seed-"
EMPTY_TOPICS = ["herramientas"]
LOCAL_HOSTS = {"localhost", "127.0.0.1"}
WORDS_PER_MINUTE = 200  # el mismo cálculo que Post.reading_minutes


def is_local_database(url: str | None) -> bool:
    if not url:
        return False
    try:
        return make_url(url).host in LOCAL_HOSTS
    except Exception:
        return False


# (título, tema, día, mes 1-12, año, minutos, bajada, cuerpo)
# Cuerpo None: se arma con FEATURED_BLOCKS a través del conversor de Notion.
# El primero es el destacado.
POSTS = [
    (
        "Concurrencia sin miedo: async en Python 3.14", "concurrencia", 14, 11, 2026, 12,
        "TaskGroup, cancelación y por qué el event loop no es magia: lo que aprendí migrando el sync de Notion a async.",
        None,  # FEATURED_BLOCKS
    ),
    (
        "Un design system para dos sitios", "design system", 2, 11, 2026, 8,
        "Cómo la landing y el blog comparten tokens sin compartir código.",
        """## Dos sitios, una voz

La landing y el blog tienen objetivos distintos: una presenta, el otro se lee. Igual tenían que sentirse parte de lo mismo.

## Tokens, no componentes

Lo que se comparte son decisiones: colores por rol, escala de espacios, radios y tipografía. Cada sitio implementa sus propios componentes sobre esos valores.

```css
:root {
  --color-accent: #0088b0;
  --space-4: 20px;
  --radius-md: 2px;
}
```

## Qué se rompe y qué no

Cuando un sitio cambia un componente, el otro no se entera, y está bien. Cuando cambia un token, los dos se mueven juntos.
""",
    ),
    (
        "Locks, colas y otras formas de esperar", "concurrencia", 21, 10, 2026, 10,
        "Primitivas de sincronización con ejemplos que sí fallan.",
        """## Esperar bien

Casi todos los errores de concurrencia son esperas mal hechas: alguien no espera cuando debía, o espera algo que nunca va a llegar.

## Un lock que no alcanza

Un lock protege una sección crítica, pero solo si todos los que la tocan lo usan. Basta un camino que lo saltee para volver al problema original.

```python
lock = asyncio.Lock()

async def increment(counter):
    async with lock:
        value = counter["n"]
        await asyncio.sleep(0)
        counter["n"] = value + 1
```

## Colas como contrato

Una cola separa a quien produce de quien consume. El contrato es simple: lo que entra sale, en orden, una sola vez.
""",
    ),
    (
        "Mudarse con una mochila", "life", 3, 10, 2026, 5,
        "Tres meses, dos ciudades y una lista de cosas que no extrañé.",
        """## La lista

Antes de salir hice una lista de todo lo que creía necesitar. A la semana la mitad sobraba.

## Lo que sí extrañé

Una buena silla, una pava eléctrica y la costumbre de saber dónde queda cada cosa.

```text
mochila 40 l
  3 remeras
  1 campera
  laptop + cargador
```

## Lo que aprendí

Menos cosas no es menos vida. Es menos tiempo decidiendo qué llevar.
""",
    ),
    (
        "Tokens que sobreviven a un rediseño", "design system", 18, 9, 2026, 7,
        "Nombrar por rol y no por color: la decisión que hizo posible este cambio.",
        """## El nombre es la decisión

Un token llamado `--amber` muere con el ámbar. Un token llamado `--color-accent` sobrevive a cualquier color nuevo.

## El rediseño como prueba

Pasar de un tema oscuro a uno claro fue, en buena parte, cambiar valores sin tocar nombres.

```css
/* antes */
--amber: oklch(0.78 0.13 70);
/* después */
--color-accent: #0088b0;
```

## Lo que no sobrevivió

Los tokens que describían una apariencia en vez de un rol. Esos hubo que reescribirlos.
""",
    ),
    (
        "El GIL ya no es excusa", "concurrencia", 30, 8, 2026, 9,
        "Free-threading en la práctica: benchmarks honestos en una máquina común.",
        """## Qué cambió

Con la build sin GIL, varios hilos de Python pueden ejecutar bytecode al mismo tiempo. No es magia: hay costos y hay bibliotecas que todavía no están listas.

## Un benchmark honesto

Medí un cálculo de CPU puro con uno, dos y cuatro hilos, en una laptop común.

```python
from concurrent.futures import ThreadPoolExecutor

def work(n):
    return sum(i * i for i in range(n))

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(work, [5_000_000] * 4))
```

## Cuándo conviene

Cuando el trabajo es de CPU y se reparte bien. Si el cuello de botella es la red, el GIL nunca fue el problema.
""",
    ),
    (
        "Un año escribiendo en público", "life", 12, 12, 2025, 4,
        "Lo que cambió al publicar aunque nadie lea.",
        """## Publicar sin público

Los primeros meses nadie leía. Escribir igual me obligó a pensar mejor lo que hacía.

## La constancia

No se trata de escribir mucho, sino de volver. Un post corto por mes alcanza.

```text
2025: 6 posts
lectores: casi nadie
ideas más claras: todas
```

## Lo que sigue

Seguir escribiendo, con menos miedo a que esté incompleto.
""",
    ),
]

# — El destacado, como bloques de Notion (la forma de la API, solo las claves
#   que lee el conversor) —

def _rt(content, href=None, **annotations):
    return {"type": "text", "plain_text": content, "href": href, "annotations": annotations}


def _block(kind, *rich_text, children=None, **data):
    block = {"type": kind, kind: {"rich_text": list(rich_text), **data}, "has_children": bool(children)}
    if children:
        block["children"] = children
    return block


FEATURED_BLOCKS = [
    _block("paragraph", _rt(
        "Durante meses el sync con Notion corrió en serie: una página, una request, una espera. "
        "Funcionaba, pero cada post nuevo sumaba segundos. Migrarlo a async parecía trivial hasta "
        "que dejó de serlo.")),
    _block("heading_1", _rt("El problema")),
    _block("paragraph",
        _rt("La API de Notion es lenta y paginada. El cuello de botella nunca fue el CPU, sino "),
        _rt("esperar", bold=True),
        _rt(". Eso es exactamente lo que "), _rt("asyncio", italic=True),
        _rt(" sabe hacer bien: esperar muchas cosas a la vez.")),
    _block("code", _rt(
        "async def fetch_all(urls):\n"
        "    async with asyncio.TaskGroup() as tg:\n"
        "        tasks = [tg.create_task(get(u)) for u in urls]\n"
        "    return [t.result() for t in tasks]"), language="python"),
    _block("paragraph",
        _rt("Con "), _rt("TaskGroup", code=True),
        _rt(", si una tarea falla, las demás se cancelan. Ese detalle cambió por completo cómo "
            "pensaba los errores.")),
    _block("quote", _rt(
        "La concurrencia no hace el código más rápido; hace que la espera deje de ser tu problema.")),
    _block("heading_3", _rt("Lo que no podía romperse")),
    _block("paragraph", _rt("Antes de migrar anoté lo que tenía que seguir funcionando:")),
    _block("bulleted_list_item", _rt("Que un post roto no corte el sync de los demás.")),
    _block("bulleted_list_item", _rt("Que la base nunca quede "), _rt("a medias", bold=True), _rt(":"),
        children=[
            _block("bulleted_list_item", _rt("si falla una página, no se escribe nada de ese post;")),
            _block("bulleted_list_item", _rt("si se corta la conexión, se reintenta desde cero.")),
        ]),
    _block("bulleted_list_item", _rt("Que el orden no dependa de qué respuesta llega primero.")),
    _block("heading_2", _rt("Event loop en cinco minutos")),
    _block("paragraph",
        _rt("Un solo hilo, una cola de tareas y una regla: nadie bloquea. Cada "),
        _rt("await", italic=True),
        _rt(" es una promesa de devolver el control. Romper esa promesa con una llamada síncrona "
            "congela todo lo demás.")),
    _block("numbered_list_item", _rt("La tarea corre hasta su primer "), _rt("await", code=True), _rt(".")),
    _block("numbered_list_item", _rt("Cede el turno y el loop avanza otra tarea que esté lista.")),
    _block("numbered_list_item", _rt("Cuando llega la respuesta, la tarea vuelve a la cola."),
        children=[
            _block("bulleted_list_item", _rt("El orden de vuelta no está garantizado.")),
            _block("bulleted_list_item", _rt("Por eso los resultados se ordenan al final.")),
        ]),
    _block("paragraph",
        _rt("La "), _rt("documentación de asyncio", href="https://docs.python.org/3/library/asyncio.html"),
        _rt(" lo explica mejor que yo. "),
        _rt("Al principio pensé que con threads alcanzaba.", strikethrough=True),
        _rt(" No alcanzaba.")),
    _block("divider"),
    _block("heading_2", _rt("Cuándo no usar async")),
    _block("paragraph",
        _rt("Si el trabajo es de CPU, async no ayuda. Ahí entran los procesos, o ahora, el "),
        _rt("free-threading", bold=True, italic=True), _rt(" de 3.14.")),
    _block("paragraph",
        _rt("Un detalle del conversor: escribir <script>, *asteriscos* o _guiones_ en Notion no rompe "
            "nada; llegan tal cual.")),
]


# Párrafos de relleno para acercar los minutos de lectura a los del diseño.
FILLER = [
    "Este párrafo es relleno de desarrollo: existe para que el post tenga el largo que muestra el diseño y se puedan probar la lectura, el índice y el desplazamiento.",
    "La idea se repite a propósito. Un texto largo deja ver cómo se comporta la columna de lectura, el tamaño de letra ajustable y el panel con el índice del artículo.",
    "Cuando el post real reemplace a este, el relleno desaparece con él. Mientras tanto, ayuda a revisar el ritmo vertical de la prosa y el espacio entre secciones.",
    "Un párrafo más para sumar palabras. El cálculo de minutos usa unas doscientas palabras por minuto y deja afuera los bloques de código, que se estudian más de lo que se leen.",
]


def _words(markdown: str) -> int:
    # misma regla que Post.reading_minutes: el código no cuenta
    import re
    return len(re.sub(r"```.*?```", "", markdown, flags=re.S).split())


def _body(excerpt: str, body: str, minutes: int) -> str:
    """Bajada como primer párrafo (Post.summary la toma de ahí) + cuerpo + relleno."""
    text = f"{excerpt}\n\n{body.strip()}\n"
    target = minutes * WORDS_PER_MINUTE
    if _words(text) < target:
        text += "\n## Notas de desarrollo\n"
        fill = cycle(FILLER)
        while _words(text) < target:
            text += f"\n{next(fill)}\n"
    return text


def seed_posts(db) -> list[Post]:
    """Inserta o actualiza los posts de muestra. Idempotente."""
    categories = {c.name: c for c in db.query(Category).all()}
    existing = {
        p.notion_id: p
        for p in db.query(Post).filter(Post.notion_id.like(f"{SEED_PREFIX}%")).all()
    }
    now = datetime.now()
    result = []

    for index, (title, cat_name, day, month, year, minutes, excerpt, body) in enumerate(POSTS):
        category = categories.get(cat_name)
        if category is None:
            category = Category(name=cat_name, slug=slugify(cat_name))
            db.add(category)
            categories[cat_name] = category

        slug = slugify(title)
        if body is None:
            body = blocks_to_markdown(FEATURED_BLOCKS)
        markdown = _body(excerpt, body, minutes)
        content_html, content_toc = render_markdown(markdown)
        notion_id = f"{SEED_PREFIX}{slug}"[:36]

        post = existing.get(notion_id) or Post(notion_id=notion_id)
        post.title = title
        post.slug = slug
        post.content_markdown = markdown
        post.content_html = content_html
        post.content_toc = content_toc
        post.published_at = datetime(year, month, day, 10, 0)
        post.featured = index == 0
        post.synced_at = now
        post.category = category
        db.add(post)
        result.append(post)

    for name in EMPTY_TOPICS:
        if name not in categories:
            db.add(Category(name=name, slug=slugify(name)))

    db.commit()
    return result


def clear_seed_posts(db) -> tuple[int, int]:
    """Borra los posts `seed-…` y los temas que quedaron sin posts por eso."""
    posts = db.query(Post).filter(Post.notion_id.like(f"{SEED_PREFIX}%")).all()
    touched = {p.category_id for p in posts}
    touched |= {c.id for c in db.query(Category).filter(Category.name.in_(EMPTY_TOPICS)).all()}
    for post in posts:
        db.delete(post)
    db.flush()

    removed_categories = 0
    for category in db.query(Category).filter(Category.id.in_(touched)).all():
        if not db.query(Post.id).filter(Post.category_id == category.id).first():
            db.delete(category)
            removed_categories += 1

    db.commit()
    return len(posts), removed_categories
