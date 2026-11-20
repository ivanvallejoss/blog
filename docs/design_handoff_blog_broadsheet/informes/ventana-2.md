# Ventana 2 · Portada y archivo — informe de cierre

La portada y el archivo están listos en la rama `broadsheet`, en 8 commits, sin push ni merge. Contra el prototipo, la portada queda a ±1 px y el archivo a 1–3 px, en 390 y en 1280. El swap de HTMX, el estado de carga y los toasts se probaron en Chromium headless.

## 1. Qué quedó hecho, por archivo

- **`app/__init__.py`** (nuevo, vacío): con eso `uv run fastapi dev app/main.py` arranca.
- **`app/models/post.py`**: `summary` recorta a 160 caracteres, contando el «…» (constante `SUMMARY_MAX`). Comentario del «rail» corregido.
- **`app/render.py`**: comentarios del «rail» corregidos.
- **`app/seed.py`** y **`cli.py`**: comando `seed-dev`.
  - Carga los 7 posts del prototipo con sus títulos, bajadas, fechas y temas; el primero queda destacado.
  - El cuerpo es markdown con h2, h3 y un bloque de código, pasado por `render_markdown`. La bajada va como primer párrafo, así `summary` devuelve la del diseño.
  - Cada cuerpo se completa con párrafos de relleno bajo un h2 «Notas de desarrollo» hasta llegar a los minutos del diseño (12, 8, 10…).
  - `notion_id` lleva el prefijo `seed-`. Es idempotente: si los posts ya existen, los actualiza.
  - `--clear` borra solo esos posts y los temas que quedan vacíos por eso.
  - Se niega a correr si `DATABASE_URL` no apunta a localhost o 127.0.0.1.
  - La ayuda avisa que `sync` los borra.
- **`app/selectors.py`**:
  - `get_tag_counts` ya no devuelve la entrada «ALL».
  - Nuevos: `get_posts_by_year(db, category_id=None)` y `group_posts_by_tag(posts, tags)`.
  - Eliminado `get_archive_counts`.
- **`app/routers/blog.py`**:
  - `/archivo/` (nombre `archive`) se registra antes que `/{category_slug}/`.
  - Las dos rutas comparten `_archive_response` y devuelven siempre la página completa, sin rama especial para HTMX.
  - Un tema que existe pero no tiene posts igual muestra su filtro, con 0.
- **`app/i18n.py`** y **`app/templating.py`**:
  - `count_line` pasó a pares singular/plural (`posts_one`/`posts_many`, `topics_one`/`topics_many`), con el filtro `plural`.
  - Textos nuevos: tema vacío, fallos de carga, «Reintentar», «Ver los {n}» y «Avisos».
- **Templates**:
  - `index.html` nuevo.
  - `archive.html` nuevo.
  - `partials/posts.html` nuevo, con macros.
  - Borrados `category.html` y `partials/post_list.html`.
  - `base.html`: «Archivo» apunta a `/archivo/` y lleva `aria-current` según `nav_active`. Se sumaron la barra de carga y el contenedor de toasts.
  - `partials/brand.html`: `brand()` y `back_button()` aceptan `class`.
- **`static/css/blog.css`** y **`blog-tokens.css`**:
  - Estilos de portada, archivo, carga y toasts. Las medidas nuevas van en el bloque marcado de `blog-tokens.css`.
  - Arreglé `.desktop-only`, que usaba `display: revert` y le sacaba el `inline-flex` a un `.btn`. Ahora `.desktop-only` y `.mobile-only` ocultan en el tamaño que no corresponde, sin tocar el display en el otro.
- **`static/js/`**:
  - `toast.js`: componente de toasts, conectado a `htmx:responseError` y `htmx:sendError`.
  - `loading.js`: estado de carga de los pedidos de HTMX.
  - `archive.js`: mantiene visible el filtro activo en la fila de mobile.
- **`static/fonts/`**: Source Serif 4 rehecha (ver §2).

## 2. Dónde me aparté del README o de CORRECCIONES

- **Fuente con `opsz` fijo en 14.** Esto corrige una decisión de la ventana 1.
  - Google Fonts sirve Source Serif 4 con el eje óptico fijo en 14, y el diseño está dibujado con esa versión. La ventana 1 había dejado el eje automático.
  - Con el eje automático, el H1 de 58 px tomaba el corte de display, más fino y angosto: entraba en 2 líneas donde el diseño usa 3.
  - Ahora las métricas coinciden glifo por glifo con las de Google, y los archivos pasaron de 245 KB a 108 KB.
- **Header del archivo.**
  - Flecha atrás solo en mobile.
  - En desktop quedan la marca y «Archivo» activo en accent-700, como D3.
  - Dejé «ivanvallejos.dev ↗», que D3 no muestra, para que el header sea igual en todas las páginas.
- **Filtros:** además de los atributos pedidos llevan `hx-select-oob="#archive-filters"`. Sin eso, el filtro activo no se actualizaba después del swap. Cada filtro tiene `id`, y HTMX devuelve el foco al mismo filtro.
- **Filas de Recientes:** 14 px de padding en mobile y 12 px en desktop, como el prototipo (el README dice 14). En las filas, los metadatos quedan en 11,5 px también en desktop, como el prototipo.
- **Botón «Leer artículo»:** lleva `aria-hidden` y `tabindex="-1"`, porque el H1 ya es el link al post. Así el teclado y el lector de pantalla no encuentran el mismo link dos veces.
- **Bloques por tema (desktop):**
  - Se muestran todos los temas con posts, de más a menos posts, en filas de tres.
  - Cada bloque muestra hasta 3 títulos y, si el tema tiene más, «Ver los N →».
  - El nombre del tema lleva a su archivo.
  - Un tema con un solo post se muestra igual que los demás.
- **Otros:**
  - «Todo» sin cantidad.
  - La línea de conteo siempre muestra los totales, con singular y plural.
  - Toasts en desktop: centrados, con un máximo de 480 px. El README no lo especifica.
  - Tema vacío: textos propios, porque el diseño solo trae la variante en inglés.

## 3. Qué afecta a las ventanas siguientes

- **La base local tiene, además de los 7 posts de muestra, el post real «Parte del Proceso» y tres temas sin posts** (`web`, `test`, `nueva-pagina`). Por eso el archivo muestra «8 posts · 4 temas» y no el «7 posts · 3 temas» del prototipo. `/web/` sirve para probar el tema vacío.
- **Un `sync` borra los posts de muestra.** Después de cada sync hay que volver a correr `seed-dev`.
- **Los posts de muestra tienen relleno.** Sirve para probar scroll y TOC en la ventana del artículo. Su TOC incluye «Notas de desarrollo».
- **Toasts para otros scripts:** `window.blogToast.success(msg)` y `blogToast.error(msg, {actionLabel, onAction})`. Las dos devuelven la función que cierra el toast. El texto lo tiene que pasar el template: el script no tiene ninguno escrito. Para «Copiado» no hay todavía una clave en `STRINGS`; la ventana del artículo tiene que crearla.
- **El log del servidor sigue mostrando todo el SQL** (`echo=True` en `app/database.py`) y llena la salida. No lo toqué porque está fuera de alcance.
- **Pendientes que siguen igual:** el handler de excepciones de Starlette y los `detail` en español de los routers.

## 4. Qué verifiqué y qué quedó sin verificar

- **Rutas**, con curl: `/`, `/archivo/`, los cuatro temas, `/web/` (tema vacío) y los posts responden 200; `/no-existe/` responde 404. El log no tiene excepciones ni 404 de estáticos.
- **Contenido de cada URL:** cada una devuelve un `#listing` con los años y posts correctos, y el filtro activo con `aria-current`.
- **Comparación con el prototipo:** capturas headless a 390×844 y 1280×800, comparadas por imagen y midiendo la posición de cada elemento. Portada en los dos tamaños: ±1 px. Archivo en desktop: lista y filtros a 1–3 px. Archivo en mobile: 1–2 px.
- **Swap real, con Playwright y el Chromium del sistema** (Playwright corrido con `uvx`, sin descargar navegadores):
  - Con teclado (foco en el filtro + Enter) cambian la URL, el título, la lista, la clase `btn-primary` y `aria-current`, y el foco vuelve al filtro.
  - El botón atrás del navegador restaura el archivo.
  - Probé los cinco filtros en orden.
- **Carga:** con la respuesta demorada, `html.is-loading` está activo, `#listing` tiene `aria-busy` y opacidad 0,4, el filtro tiene `htmx-request` y el ícono gira. Todo se limpia al terminar. Con `prefers-reduced-motion`, el giro y la transición se apagan.
- **Fallo:** el corte de servidor lo simulé abortando la conexión. El toast de error aparece con `role="alert"` y «Reintentar», y sigue ahí a los 3 s. Al tocar «Reintentar» con el servidor de vuelta, el pedido se completa y el toast desaparece. Una respuesta 500 también muestra el toast.
- **Toasts:** el de éxito desaparece entre los 2,7 y los 3,3 s. Las posiciones coinciden con el diseño (40 px y 118 px del borde, 16 px a los costados, 56 px de alto).
- **Áreas táctiles:** todos los filtros llegan a 44 px o más.
- **Sin verificar:**
  - La captura visual del estado de carga. Los valores se verificaron por estilos computados, pero la captura salió con el swap ya hecho.
  - Navegadores que no sean Chromium.
  - Lector de pantalla real.
  - El corte de servidor real: lo simulé abortando la conexión.

## 5. Qué quedó disponible para las ventanas siguientes

- **Variable de template:** `{% set nav_active = "archive" %}` marca «Archivo» en el header.
- **Macros** (en `partials/posts.html`, importar `with context`): `post_url(post)`, `post_meta(post)`, `post_row(post)` y `empty_state(title, body)`.
- **Macros de `partials/brand.html`:** `brand()` y `back_button()` aceptan `class`.
- **Filtro de Jinja:** `t | plural("posts", n)`.
- **Clases de listas y estados:** `.post-row` (y `__title` / `__meta`), `.empty-state`, `.archive-row` (y sus partes), `.archive-filter` y `.load-bar`.
- **Estados de carga:** `[aria-busy="true"]` baja al 40 % cualquier elemento. `.is-loading` en `<html>` muestra la barra de carga.
- **Toasts:** `.toasts` y `.toast` (con `--success` / `--error`).
- **Tokens:** los de portada, archivo y estados, en `blog-tokens.css`.
- **JavaScript:**
  - `window.blogToast.show({type, message, actionLabel, onAction, duration})`, más los atajos `.success()` y `.error()`.
  - `[data-toast-error]` en el elemento que dispara un pedido HTMX (o en un ancestro) define el mensaje si ese pedido falla.
  - `loading.js` funciona para cualquier pedido HTMX.
