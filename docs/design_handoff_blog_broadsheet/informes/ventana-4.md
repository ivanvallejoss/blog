# Ventana 4 · Búsqueda y páginas de error — informe de cierre

La búsqueda y las páginas de error están en la rama `broadsheet`, en 11 commits, sin push ni merge. Con esto el blog en español queda completo. Contra el prototipo, la búsqueda de desktop, la 404 de desktop y el número y el H1 de las páginas de mobile coinciden al décimo de píxel. Pasan 73 pruebas unitarias, 46 comprobaciones nuevas con Playwright y las 65 de la ventana 3.

## 1. Qué quedó hecho, por archivo

- **`app/templating.py`**: `url_for` en los templates devuelve solo la ruta (`url_path_for`). Cubre todos los links, incluidos los filtros, `hx-get`, «Siguiente» y los estáticos.
- **`app/config.py`**: `BASE_URL`, que sale de `BLOG_BASE_URL`.
- **`app/routers/blog.py`**:
  - `share_url` se arma con `BASE_URL` si está definida (`_absolute_url`).
  - Nuevo `GET /search.json` (nombre `search_index`), registrado antes que la categoría, con `Cache-Control: public, max-age=300`.
  - Los `detail` son claves del diccionario.
- **`app/search.py`** (nuevo): `build_search_index(posts, lang, post_path)` y `search_entry()`.
  - Cada entrada trae lo que pide el README, más `url`, `date_label` («14 NOV») y `meta_label` («14 NOV · concurrencia · 12 min»).
  - Con `lang=en` devuelve una lista vacía; un idioma desconocido cae en español.
- **`app/selectors.py`**: `get_recent_posts(db, limit=None)`, del más nuevo al más viejo.
- **`app/main.py`** (reescrito):
  - Manejador de la `HTTPException` de Starlette. La 404 usa su plantilla; cualquier otro código, la genérica.
  - Manejador de `Exception`, que responde 500 sin tocar la base.
  - Una referencia corta (`7f3a-20nov-0943`) en la página y en el log, con la traza.
  - «Quizás buscabas» a prueba de base caída.
- **`app/i18n.py`**: 11 claves nuevas para búsqueda y errores, en ES y EN.
- **`notion/client.py`**: `get_posts` sigue el cursor.
- **Templates:**
  - `base.html`:
    - El script en línea que pone `.has-js`.
    - Carga `dialog.js` y `search.js`.
    - Incluye el partial de búsqueda.
    - Respeta `hide_search`.
  - `post.html`: queda solo el script del tamaño de texto.
  - `partials/search.html` (nuevo): el diálogo.
  - `partials/errors.html` (nuevo): el macro `plate_number`.
  - `errors/404.html` y `errors/error.html`: reescritos.
  - `partials/posts.html`: `post_row` acepta `class`.
  - `partials/brand.html`: el botón de búsqueda pasa a `.js-only`.
- **`static/js/dialog.js`** (nuevo): `window.blogDialog`, con el foco atrapado en orden visual, Esc, la guarda de foco y el bloqueo de scroll que antes vivían en `article.js`.
- **`static/js/article.js`**: el panel de lectura usa `blogDialog`.
- **`static/js/search.js`** (nuevo): la búsqueda. Hasta que se abre solo escucha clics, ⌘K/Ctrl+K y envíos de formulario.
- **`static/css/blog.css` y `blog-tokens.css`**:
  - Estilos del campo de búsqueda, la búsqueda y las páginas de error.
  - Tokens nuevos en el bloque marcado.
  - `html.reader-open` pasa a ser `html.dialog-open`.
- **`tests/test_web.py`** (nuevo): 16 casos con `TestClient`, sin base.
  - El índice y su caché.
  - Las tres formas de 404.
  - La 404 con la base caída.
  - Las planchas con `aria-hidden`.
  - El 500 con su referencia y la traza en el log.
  - El 405.
  - `share_url` con y sin `BLOG_BASE_URL`.
  - Que no haya links absolutos.

## 2. Dónde me aparté del README o de CORRECCIONES, y por qué

- **Campo vacío según el ancho.** En mobile van las etiquetas de temas; en desktop, todos los posts bajo «Todos los posts», con el primero activo, como D4. Es el mismo marcado; cambia el CSS según `data-state`.
- **«Sin resultados» en desktop** no está diseñado: uso el bloque de mobile dentro del diálogo.
- **Sin «Sugerime un tema».** El link es opcional y no tiene destino.
- **«Reintentar» es un link a la misma URL, con su query,** no `location.reload()`. Así funciona sin JavaScript.
- **El 500 no ofrece búsqueda,** porque depende de la base. Es lo que hace el prototipo E1b, que no tiene lupa.
- **El 500 de desktop no está diseñado.** Usa la columna izquierda de la 404 (máximo 580 px) con los botones en fila.
- **Texto de la 404:** una URL de un segmento que no es un tema usa el texto genérico, como el prototipo con `/concurrencia-sin-mieod`. Un post inexistente dice «El post que buscás no existe o fue movido.».
- **«Quizás buscabas»** va del más nuevo al más viejo. El prototipo de desktop los muestra en otro orden.
- **Los estáticos también pasaron a ruta relativa.** Detrás del proxy, la URL absoluta con http rompía CSS y JS en https.
- **Resultado activo en mobile:** se resalta solo si se usan las flechas, porque el prototipo de mobile no lo resalta. En desktop siempre.
- **Temas de las etiquetas:** salen del índice, de más a menos posts. El README define `/search.json` como una lista y no lo cambié.
- **Sin la cruz nativa de `type=search`,** porque el diseño no la tiene.
- **Los `{n}` y `{q}`** de las plantillas de texto los completa el JavaScript, que las recibe del template en `data-*`. No tiene textos escritos.

## 3. Qué descubrí que afecta a las ventanas siguientes

- **Idioma (ventana 5):**
  - `/search.json` ya acepta `lang`. Cuando exista la columna, hay que filtrar en `build_search_index`, que hoy pone `"lang": "es"` fijo.
  - `data-index-url` ya lleva `?lang={{ lang }}`.
  - Las páginas de error usan `DEFAULT_LANG`. Con rutas `/en/`, el manejador tiene que deducir el idioma del pedido.
- **OpenGraph (ventana 6):** `config.BASE_URL` está lista para `og:url` y `og:image`.
- **Cuándo optimizar la bajada:** `Post.summary` cuesta unos 0,1 ms por post. `/search.json` tarda 10 ms con 100 posts y 100 ms con 1000. Con caché de 5 minutos, conviene guardarla en una columna a partir de unos 300 posts, o si el índice empieza a pesar en el servidor.
- **Excepciones no controladas:** Starlette vuelve a lanzarlas después del manejador, así que uvicorn también imprime la traza. En el log quedan dos trazas por error, y la referencia está en la nuestra.
- **Logging:** `app/main.py` llama a `logging.basicConfig(level=WARNING)` si el logger raíz no tiene salida. Con gunicorn, revisar que `blog.errors` llegue a su log.
- **Diálogos:** abrir un diálogo cierra el que estuviera abierto. ⌘K con el panel de lectura abierto lo cierra y abre la búsqueda.
- **Base local:** la 404 consulta la base en un hilo aparte. Si la base no responde pero acepta conexiones, el pedido puede esperar el timeout de psycopg2, que no está configurado.

## 4. Qué verifiqué, cómo, y qué quedó sin verificar

- **Pruebas:** `uv run python -m unittest`, 73 en verde (57 del conversor y 16 web).
- **Con curl:**
  - `/search.json` devuelve el JSON con la caché.
  - `/no-existe/`, `/concurrencia/nope/` y `/a/b/c/` devuelven 404 con la plantilla HTML; ninguna en JSON.
  - `POST /` devuelve 405 con la plantilla genérica.
  - El 500 lo provoqué con una segunda instancia levantada desde un script del scratchpad, con una ruta que falla. Responde 500, la referencia en la página coincide con la del log junto a la traza, y «Reintentar» apunta a la misma URL. La ruta no quedó en el código.
- **Comparación con el prototipo,** con capturas a 390×844 y 1280×800, por imagen y midiendo cada elemento:
  - Búsqueda de desktop: campo, primera fila, título y fecha a ±0,1 px.
  - Búsqueda de mobile: campo, «Cancelar» y primera fila a ±0,1 px. «Sin resultados» se ve igual.
  - 404 de desktop: número, H1, texto, campo, «Buscar» y «Quizás buscabas» a ±0,1 px.
  - 404 y 500 de mobile: número y H1 a ±0,1 px. El resto se corre por el ancho de 370 px del marco del prototipo, que hace que el texto parta en otro lugar.
- **Playwright sobre el Chromium del sistema (46 comprobaciones):**
  - El índice no se pide hasta abrir la búsqueda, y se pide una sola vez.
  - Se abre con el botón, con Ctrl+K y con ⌘K. Al abrir tiene `role="dialog"` y `aria-modal`, el foco va al campo y el fondo no scrollea.
  - ↑↓ con vuelta, el activo a la vista, un solo `aria-selected`, y Enter abre el post.
  - «CANCELACION» y «cancelación» dan lo mismo. «rediseno» encuentra «rediseño». También busca por tema.
  - La región viva anuncia la cantidad.
  - Sin resultados: el título con comillas angulares y las etiquetas. Tocar una etiqueta la busca.
  - Lo cierran Esc, el velo y «Cancelar», y el foco vuelve a quien abrió.
  - El foco no sale del diálogo.
  - Fallo del índice: aparece el toast con «Reintentar», se llega con Tab, y al usarlo carga el índice y el diálogo sigue abierto.
  - El campo de la 404 abre la búsqueda con lo escrito y le devuelve el foco al cerrar.
  - En mobile ocupa la pantalla completa y el campo tiene 16 px.
  - Con `prefers-reduced-motion`, sin animación.
  - Sin JavaScript no aparecen ni el botón ni el campo de la 404.
- **Regresión:**
  - Las 65 comprobaciones del panel de lectura de la ventana 3 pasan sobre `dialog.js`.
  - Los filtros del archivo cambian la URL y la lista, y su `hx-get` es solo la ruta.
  - Un pedido de HTMX que recibe un 404 deja la lista y muestra el toast de fallo.
- **Links:** ningún link interno absoluto en el HTML de portada, archivo, tema, tema vacío, post, 404 y 500.
- **Sin verificar:**
  - Lector de pantalla real (el combobox y la región viva).
  - Safari de iOS: el teclado virtual con la barra sticky y el bloqueo de scroll.
  - Navegadores que no sean Chromium.
  - El 500 detrás del proxy real.
  - La base caída de verdad (lo simulé en la prueba).

## 5. Qué quedó disponible

- **Variable de template:** `{% set hide_search = true %}` quita el botón, el diálogo y el script de búsqueda.
- **Macros:**
  - `plate_number(text)`, en `partials/errors.html`.
  - `post_row(post, class)`, con `post-row--compact`.
- **Partial:** `partials/search.html`.
- **Python:**
  - `app.search.build_search_index` y `search_entry`.
  - `selectors.get_recent_posts`.
  - `config.BASE_URL`.
  - `templating.url_path_for`, que es el `url_for` de los templates.
  - `routers.blog._absolute_url`.
- **Clases:**
  - Campo de búsqueda: `.search-field` (con `__icon` y `__input`).
  - Búsqueda: `.search` (con `[data-state]` y `.uses-keys`), `.search__panel`, `__bar`, `__body`, `__count`, `__results`, `__none`, `__topics`, `__foot`, `.search-option` (y sus partes) y `.search-chip`.
  - Errores: `.error-page` (con `--404` y `--generic`), `__number`, `__title`, `__body`, `__side`, `__actions`, `__action`, `__ref`, `__home` y `.error-search`.
  - Global: `html.dialog-open`.
- **Tokens:** `--search-*` y `--error-*`.
- **JavaScript:**
  - `window.blogDialog.create({element, setModal, onOpen, onClose})` → `{open(opener), close(returnFocus), isOpen()}`.
  - `window.blogSearch.open(texto, elementoQueAbre)`.
  - `[data-search-open]` abre la búsqueda; `[data-search-form]` la abre con el valor de su campo.

## 6. Pasos a mano en el servidor al desplegar

Los de la ventana 3, sin cambios:

1. No hay migraciones ni dependencias nuevas.
2. Correr una vez `uv run python cli.py sync --force` y revisar qué tipos no soportados informa.
3. Para ver el SQL en el log, `BLOG_SQL_ECHO=1`.
4. `--proxy-headers` y `--forwarded-allow-ips` en uvicorn o gunicorn. Con esta ventana ya no afecta a la navegación, pero sí a `share_url` si no se define el paso siguiente.
5. Purgar la caché de Cloudflare de los estáticos.

Y los de esta ventana:

6. Definir `BLOG_BASE_URL=https://blog.ivanvallejos.dev` en el entorno del servidor, para que compartir use la URL pública sin depender del proxy.
7. Sumar a la purga: `blog.css`, `blog-tokens.css` y `article.js` cambiaron, y `dialog.js` y `search.js` son nuevos.
8. Revisar que el log del servidor reciba las líneas de `blog.errors`, con su `[ref …]`. Si gunicorn lo configura de otra forma, sumar ese logger a su configuración.
9. Si Cloudflare cachea JSON, `/search.json` ya manda `max-age=300`: no hace falta una regla aparte.
