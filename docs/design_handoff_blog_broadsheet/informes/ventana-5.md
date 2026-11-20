# Ventana 5 · Idioma — informe de cierre

El blog es bilingüe en la rama `idioma` (salida de `main` en `66f5c8f`), en 11 commits, sin push ni merge. Las URLs en español no cambian; el inglés vive bajo `/en/`. Pasan 122 pruebas unitarias (49 nuevas), 51 comprobaciones nuevas con Playwright y, con el flag apagado, las 65 de la ventana 3 y las 46 de la ventana 4.

## 1. Qué quedó hecho, por archivo

- **`cli.py`**:
  - `seed-dev` exige `BLOG_ALLOW_SEED=1`, además de una base local. Sin la variable se niega y dice cuál falta.
  - `sync` informa los `Idioma` desconocidos y los temas con slug reservado.
- **`app/config.py`**: `SEED_ALLOWED`.
- **`alembic/versions/a7c41e9b2d05_…`**: suma `posts.lang` (`varchar(2)`, no nulo, `'es'` por defecto, índice `ix_posts_lang`, `CHECK ck_posts_lang`) y `posts.excerpt` (`text`, opcional). Los posts existentes quedan en español.
- **`app/models/post.py`**:
  - Columnas `lang` y `excerpt`.
  - `summary` devuelve `excerpt` si tiene texto. Si no, devuelve `derived_summary`, que es la bajada de antes.
- **`app/i18n.py`**:
  - `LANG_PREFIX`, `normalize_lang`, `other_lang` y `lang_from_path`. Este último es el único lugar que deduce el idioma.
  - `TOPIC_NAMES[lang][slug]` y `topic_name(tema, lang)`.
  - `plural` acepta más campos y devuelve Markup escapado.
  - Claves nuevas: `anchor_title`, `lang_empty_*` y `see_in_this_lang`.
- **`app/urls.py`** (nuevo):
  - La tabla `PAGES`, con el nombre lógico y la ruta por idioma.
  - `route_name`, `is_page` y `registration_order`: las rutas fijas primero, después las `/en/…` con parámetros y al final las del español.
  - `RESERVED_TOPIC_SLUGS`: `en`, `archivo`, `archive`, `search.json` y `static`.
- **`app/routers/blog.py`**:
  - Cada página se registra una vez por idioma (`archive.es`, `archive.en`) con el mismo manejador. El idioma llega por `request_lang`.
  - Los contextos llevan `other_count`, para el estado vacío por idioma.
  - `/search.json?lang=` filtra por idioma.
  - Sale `_absolute_url` y lo reemplaza `templating.absolute_url`.
- **`app/selectors.py`**:
  - Todos los listados reciben `lang`: portada, recientes, temas, archivo, post por slugs y «Siguiente», que toma el idioma del propio post.
  - `get_tag_counts` ordena por el nombre del tema en ese idioma.
  - Nuevo: `count_posts(db, lang, category_id=None)`.
- **`app/search.py`**: descarta los posts de otro idioma. `category` y `meta_label` llevan el nombre traducido, y `lang` sale del post.
- **`app/main.py`**: la 404 y la página genérica salen en el idioma de la ruta, con el `detail` y «Quizás buscabas» de ese idioma.
- **`app/templating.py`**:
  - El `url_for` de los templates resuelve las páginas en el idioma en curso. `lang=` pide otro idioma.
  - Ayudantes `page_path` y `absolute_url`.
  - El contexto común suma `other_lang`, `t_other`, `lang_urls`, `lang_homes` y `hreflang`.
  - Filtros nuevos: `topic` y `em`.
- **`app/render.py`**: una instancia de Markdown por idioma. `render_markdown(md, lang)` escribe el `title` del ancla en el idioma del post. Lo usan el sync, `seed-dev` y `backfill-db`.
- **`notion/client.py`**: `read_lang`, `_select_name` y `_rich_text`. `Idioma` y `Resumen` pueden faltar, venir vacías o tener otro tipo.
- **`sync/services.py`**: guarda `lang` y `excerpt`. `SyncReport` suma `unknown_lang` y `reserved_topics`.
- **`app/seed.py`**:
  - `POSTS_EN`: cinco posts en inglés con la bajada en `excerpt` y un cuerpo que empieza con otro párrafo.
  - `life` queda solo en español y `herramientas` sigue sin posts.
  - Relleno y «Development notes» en inglés.
- **Templates**:
  - `base.html`: `hreflang` y el switch.
  - `partials/brand.html`: el switch son dos `<a>` con `hreflang`, `lang` y `aria-current`, dentro de `#lang-switch`.
  - `partials/posts.html`: `lang_empty_state`, `empty_state` con `caller` y `post_url` con el idioma del post.
  - `index.html`, `archive.html`, `post.html`: nombres de tema traducidos y el estado vacío por idioma. Los filtros traen el switch por `hx-select-oob`.
  - `errors/*.html`: `error_page`.
- **`static/css/blog.css`** y **`blog-tokens.css`**:
  - El switch como links, con el corrimiento de mobile resuelto (ver §2).
  - `.empty-state__action`.
  - Tokens nuevos: `--lang-switch-sep-offset` y `--empty-action-gap`.
- **Pruebas**:
  - `tests/test_lang.py` (nuevo, 37 casos).
  - `tests/test_notion.py` (nuevo, 12 casos).
  - `tests/test_web.py` ajustado.

## 2. Dónde me aparté del README o de CORRECCIONES, y por qué

- **Switch:** dos links reales en vez de `<button>`, y sin `localStorage`. Lo decidiste en el brief.
- **Switch en mobile:**
  - Dos áreas de 44 px no entran sin pisarse con la geometría del prototipo. El texto, de ES a la lupa, ocupa 52 px y hacen falta 88.
  - EN conserva el padding del diseño y su área crece hacia la izquierda, sobre la barra. ES mide 44 px con el texto contra el borde donde empieza EN.
  - Medido con Playwright: EN y «/» quedan exactos y ES queda 6,4 px a la izquierda. Antes ES y EN estaban 18 px corridos. Las dos áreas miden 44×44 y no se pisan.
- **E3b:** el prototipo muestra «life» como filtro activo en inglés y el conteo «7 posts · 3 topics». Los filtros y conteos son por idioma y, como decidió la ventana 3, solo se ofrecen temas con posts. En `/en/life/` el filtro no aparece y ningún filtro queda marcado.
- **Botón del estado vacío:** se escribe en el idioma de destino («Ver en español» / «See in English»), con `lang` en el link, como el prototipo.
- **Título del estado vacío:** «No posts in English here yet» sirve para portada, archivo y tema. En español: «Todavía no hay posts en español acá». Sin tema, el texto es «There are N posts in Spanish.».
- **`hreflang`:**
  - Va también con el flag apagado, porque las rutas en inglés existen siempre.
  - `x-default` apunta al español.
  - El tema vacío también lo lleva.
  - Las URLs son absolutas: con `BLOG_BASE_URL` si está definida y, si no, desde el pedido.
- **`/en/archive/`**, como el README §8. La barra del prototipo D3 dice `/en/archivo`.
- **Slug reservado `static`:** lo sumé a los cuatro del brief, porque ahí vive el montaje de estáticos.
- **Ancla «#»:** cambia solo el `title`. Su nombre accesible sigue siendo «#», como anotó la ventana 3.

## 3. Qué afecta a la ventana de OpenGraph

- **URL absoluta:** `templating.absolute_url(request, path)`. Es la misma que arma `share_url` y `hreflang`. `routers.blog._absolute_url` ya no existe.
- **Idioma del post:** `Post.lang` sirve para `og:locale` (falta elegir `es_AR` o `es_ES`). `og:locale:alternate` solo tiene sentido en portada, archivo y tema; el contexto `hreflang` ya trae esas URLs.
- **Descripción:** `Post.summary` ya devuelve el `Resumen` de Notion si existe. Sirve directo para `og:description` y `<meta name="description">`.
- **Tema en la imagen:** tiene que salir en el idioma del post, con `topic_name(post.category, post.lang)`.
- **Imagen por defecto:** su frase está en español («Notas de Iván Vallejos sobre…»). La portada y el archivo en inglés necesitan otra versión o una sin texto.
- **`static/og/{slug}.png`** sirve igual en los dos idiomas, porque `Post.slug` es único en toda la tabla.
- **Sin `BLOG_BASE_URL`,** `hreflang` sale con el esquema del pedido. Detrás del proxy puede quedar en http, igual que `og:url`.

## 4. Qué verifiqué, cómo, y qué quedó sin verificar

- **Pruebas:** `uv run python -m unittest`, 122 en verde. Cubren:
  - Las ocho rutas.
  - Un post bajo el idioma equivocado (404 en los dos sentidos).
  - El índice por idioma y su nombre de tema traducido.
  - `topic_name` con y sin traducción.
  - `Idioma` y `Resumen` ausentes, vacías, con otro tipo o con valor desconocido, también a través de `sync_posts`.
  - Los slugs reservados.
  - El switch, `hreflang`, el estado vacío y la 404 y la página genérica bajo `/en/`.
- **Migración:** aplicada en la base local (puerto 5435), bajada y vuelta a subir. `alembic check` no detecta diferencias con el modelo y los 8 posts que había quedaron en `es`.
- **Con curl:**
  - Las ocho rutas, `/en/life/` y `/en/herramientas/` responden 200.
  - `/en/a/b/c/`, `/en/no-existe/` y un post en español bajo `/en/` responden 404, con la plantilla en inglés.
  - `/search.json?lang=en` trae los 5 posts en inglés y `?lang=es` los 8 en español.
  - `/en` y `/archivo` redirigen con la barra.
- **Capturas** a 390×844 y 1280×800 de la portada, el archivo, el artículo y el estado vacío en inglés, junto al prototipo con el switch en EN:
  - Coinciden la tipografía, la posición y los textos.
  - Diferencias esperadas: los conteos por idioma, «life» sin posts en inglés y el marco del prototipo.
- **Playwright sobre el Chromium del sistema, con el flag encendido (51 comprobaciones), en mobile y desktop:**
  - Switch en portada, archivo, tema, post y 404.
  - `aria-current`.
  - Filtro del archivo en inglés: la URL empujada es `/en/concurrencia/`, se marca el filtro activo, cambia el título y el switch pasa a apuntar al tema.
  - Botón del estado vacío.
  - Búsqueda en inglés: por «concurrency», sin posts en español, con «Nothing about…» y la fecha «30 AUG».
  - Ancla «Link to this section».
  - Sin JavaScript, el switch funciona.
- **Regresión con el flag apagado:**
  - Comparé el HTML de `main` y de `idioma` contra la misma base, sin los posts en inglés. Comparé portada, archivo, tema, tema vacío, post, post real y 404.
  - Solo cambian `hreflang`, el `hx-select-oob` y líneas en blanco. `/search.json` en español sale idéntico.
  - Pasan las 65 comprobaciones del panel de lectura y las 46 de la búsqueda.
- **`sync --force` real:** 1 reconvertido y 12 borrados (los del seed), sin errores, con la base de Notion todavía sin las propiedades nuevas. Después volví a correr `seed-dev`.
- **Sin verificar:**
  - Lector de pantalla real (el switch con `aria-current` y `lang`).
  - Navegadores que no sean Chromium, ni Safari de iOS.
  - La validez de `hreflang` en Search Console.
  - Un post real en inglés que venga de Notion: no hay ninguno todavía.
  - El switch de desktop solo lo comparé por imagen; su CSS no cambió.

## 5. Qué quedó disponible

- **Idioma:** `lang_from_path(path)`, `other_lang(lang)`, `normalize_lang(value)`, `LANG_PREFIX` y `topic_name(tema, lang)`. Todo en `app/i18n.py`.
- **Diccionario de temas:** `TOPIC_NAMES["en"][slug]`. Agregar ahí cada tema nuevo, por ejemplo `presentacion`, que hoy sale con su nombre original.
- **URLs:**
  - En templates: `url_for('archive')` en el idioma en curso y `url_for('archive', lang='en')` para otro.
  - En Python: `page_path(request, nombre, lang, **params)`, `absolute_url(request, path)` y `routers.blog.post_path(request, post)`.
  - Tabla y orden: `app/urls.py` (`PAGES`, `route_name`, `registration_order` y `RESERVED_TOPIC_SLUGS`).
- **Contexto de los templates:** `lang`, `other_lang`, `t`, `t_other`, `lang_urls`, `lang_homes` y `hreflang`. `{% set error_page = true %}` manda el switch a las portadas y quita `hreflang`.
- **Filtros de Jinja:** `topic(lang)`, `em` y `plural(clave, n, **campos)`, que ahora devuelve Markup.
- **Macros:**
  - `lang_switch(t, lang, langs, enabled, urls)`.
  - `lang_empty_state(count, topic=none)`.
  - `empty_state` acepta un bloque `{% call %}`.
- **Selector:** `count_posts(db, lang, category_id=None)`. Todos los demás listados reciben `lang`.
- **Render y sync:** `render_markdown(md, lang)`, `notion.client.read_lang(properties)`, `sync.services.reserved_topics(names)`, y `SyncReport.unknown_lang` y `.reserved_topics`.
- **Modelo:** `Post.lang`, `Post.excerpt` y `Post.derived_summary`.
- **Pruebas:** en `tests/test_lang.py`, los selectores falsos que filtran por idioma (`FAKES`); en `tests/test_notion.py`, la fábrica `page()` de Notion.

## 6. Pasos a mano

**En Notion** (base de posts):

1. Crear la propiedad **`Idioma`**, de tipo **Select**, con dos opciones: **`es`** y **`en`**, en minúscula. Se aceptan sin distinguir mayúsculas; cualquier otro valor cae a español y lo informa el sync. Vacía equivale a `es`.
2. Crear la propiedad **`Resumen`**, de tipo **Text**. Es la bajada escrita a mano. Vacía, se deriva del primer párrafo.
3. Una traducción es otra página, con su propio **`slug`**, distinto del original. Dos posts con el mismo slug hacen fallar el sync en la restricción `unique`. Esto ya pasaba antes de esta ventana.
4. Evitar temas que se llamen `en`, `archivo`, `archive` o `static`. El sync los informa.

**En el servidor al desplegar** (sumados a los de las ventanas 3 y 4):

1. `uv run python cli.py sync --force`, una vez, y revisar qué tipos no soportados informa (ventana 3).
2. Para ver el SQL en el log, `BLOG_SQL_ECHO=1`.
3. `--proxy-headers` y `--forwarded-allow-ips` en uvicorn o gunicorn.
4. Purgar la caché de Cloudflare de los estáticos.
5. `BLOG_BASE_URL=https://blog.ivanvallejos.dev`. Ahora también la usa `hreflang`.
6. Sumar a la purga lo de la ventana 4: `blog.css`, `blog-tokens.css`, `article.js`, `dialog.js` y `search.js`.
7. Revisar que lleguen al log las líneas de `blog.errors`.
8. `/search.json` ya manda `max-age=300`. Ahora la caché varía por `?lang=`: si Cloudflare ignora la query, configurarlo para que la respete.
9. **Nuevo:** `uv run alembic upgrade head`, para la migración `a7c41e9b2d05` (lang y excerpt). Es la primera migración desde que empezó Broadsheet.
10. **Nuevo:** no definir `BLOG_ALLOW_SEED` en el servidor.
11. **Nuevo:** el `sync --force` del paso 1 conviene correrlo después de la migración. Así cada post toma `Idioma` y `Resumen` de Notion y el ancla de los títulos queda en su idioma.
12. **Nuevo:** sumar a la purga `blog.css` y `blog-tokens.css`, que cambiaron otra vez.
13. **Nuevo:** para mostrar el switch, `BLOG_LANG_SWITCH=1`. Las rutas `/en/` existen aunque el flag esté apagado.
