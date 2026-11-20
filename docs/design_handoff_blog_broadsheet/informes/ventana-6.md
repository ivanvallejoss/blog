# Ventana 6 · OpenGraph, feed y cierre — informe

La ventana está en la rama `opengraph`, en 12 commits contando este informe, sin push ni merge. Salió de **`idioma`**, porque `idioma` no está mergeada en `main` (`main` llega hasta la ventana 4).

- Pasan 160 pruebas unitarias, 38 de ellas nuevas.
- Pasan las regresiones con Playwright de las ventanas 3, 4 y 5: 65, 46 y 51 comprobaciones.
- Las imágenes coinciden con el prototipo al píxel en vertical y a ±1,5 px en horizontal.

## 1. Qué quedó hecho, por archivo

- **`pyproject.toml` y `uv.lock`:** Pillow 13, la única dependencia nueva.
- **`app/og/`** (nuevo):
  - `tokens.py`: colores y medidas con el nombre de su token. Hace la conversión oklch → sRGB y trae los tres trazos del favicon.
  - `draw.py`:
    - Imagen de post, imagen por defecto y `apple-touch-icon`.
    - Modelo de caja de línea de Chromium, letter-spacing por carácter y kerning con libraqm.
    - Partido equilibrado del título y anillo sobremuestreado ×8.
  - `images.py`:
    - Huella de lo que muestra cada imagen, guardada dentro del PNG.
    - `refresh_images()` y `image_version()` para el `?v=`.
    - Escritura atómica.
  - `fonts/`: Source Serif 4 en opsz 14 (600, 400 e itálica 400) y Geist Mono 400, en TTF, con sus licencias OFL y un README de cómo se generaron. La carpeta no se sirve como estático.
- **`app/meta.py`** (nuevo): `PageMeta`, `listing_meta()` y `post_meta()`. Arma descripción, canonical, OpenGraph y Twitter. Si un post no tiene imagen, usa la por defecto de su idioma.
- **`app/feed.py`** (nuevo): Atom con la librería estándar.
  - Últimos 20 posts, con el contenido completo.
  - Sin el ancla «#» y con los links relativos pasados a absolutos (`urljoin`).
  - Id permanente: `urn:uuid:` con el id de Notion.
  - Fechas en UTC con `Z`.
- **`app/i18n.py`:** `site_description` (la frase, con `*énfasis*`), `archive_description`, `topic_description`, `og_post_alt`, `og_default_alt` y `feed_title`, en ES y EN. También `OG_LOCALE` (`es_AR` y `en_US`) y `plain_text()`.
- **`app/urls.py`:** página `rss` (`/rss.xml` y `/en/rss.xml`), con lo que `rss.xml` queda entre los slugs reservados.
- **`app/routers/blog.py`:** `meta` en portada, archivo, tema y post. Ruta `rss` con `Cache-Control: public, max-age=300`.
- **`app/templating.py`:** `rss_url` se detecta por idioma con `page_path`. Filtro `plain`.
- **Templates:**
  - `partials/meta.html` (nuevo).
  - `base.html`:
    - Bloque `meta`: las páginas de error llevan solo la descripción.
    - `<link rel="alternate">` al feed del idioma.
    - Link al `apple-touch-icon`.
- **`sync/services.py`:** después de guardar, `_refresh_images()` borra las imágenes de los posts borrados o que cambiaron de slug, y genera las que cambiaron. `SyncReport.images` informa las que fallaron.
- **`cli.py`:**
  - `og-images [--force]`: borra huérfanas y sale con 1 si alguna falla.
  - `touch-icon`.
  - `sync` imprime la línea de imágenes.
  - `seed-dev` genera las imágenes de los posts de muestra y `--clear` las borra.
  - Avisa si falta `BLOG_BASE_URL` o libraqm.
- **`app/seed.py`:** `clear_seed_posts` devuelve también los slugs.
- **`static/public/apple-touch-icon.png`** (nuevo, commiteado).
- **`.gitignore`:** `static/og/`.
- **Pruebas:**
  - `tests/test_og.py` (23): tokens, anillo, partido de líneas (incluidos los cortes de Chromium), 100 caracteres, cuándo se regenera y cuándo se borra (también a través de `sync_posts`), fallos e ícono.
  - `tests/test_share.py` (15): meta tags de cada tipo de página en los dos idiomas, páginas de error sin tags, URLs `https` absolutas y los dos feeds.
  - `test_lang.py` y `test_notion.py` ajustadas.
- **Docs:**
  - `README.md` de la raíz: variables, CLI, rutas, propiedades de Notion, pruebas, feed y el párrafo del markdown con HTML en línea.
  - `.env.example` (nuevo).
  - ADR de Broadsheet con el estado final.
  - `docs/despliegue-broadsheet.md` (nuevo).

## 2. Dónde me aparté del handoff o de CORRECCIONES, y por qué

- **Atom, no RSS 2.0,** en `/rss.xml`. El contenido completo tiene `<content type="html">` sin extensiones, y Atom trae ids permanentes y fechas RFC 3339. La URL no cambia.
- **Qué dispara la regeneración.** El README dice «título, tema o fecha». Uso todo lo que la imagen muestra: también los minutos, el idioma (fecha y tema traducidos), el dominio y `RENDER_VERSION`. La huella va dentro del PNG: no hace falta columna y es el `?v=` de la URL.
- **El sync revisa la huella de todos los posts,** no solo de los que tocó. Leer la cabecera de un PNG es barato, y así un cambio de `BLOG_BASE_URL` o una imagen borrada a mano se arreglan en el próximo sync. `sync --force` no fuerza las imágenes: para eso está `og-images --force`.
- **Imagen por defecto** en `static/og/default/{lang}.png`, una por idioma, y también en las páginas de tema (el README dice «portada y archivo»).
- **Título que no entra:** con 64 px y el partido equilibrado, un título que igual pisaría la marca baja de a 2 px. El margen es de 24 px y el piso de 40 px. El diseño no lo prevé. Con 100 caracteres normales no se activa; con 100 «W», sí.
- **`apple-touch-icon` cuadrado,** sin las esquinas de 40 px del prototipo: iOS aplica su propia máscara.
- **Link alternate del feed con ruta relativa.** Los lectores la resuelven contra la página, y así no depende del proxy, igual que el resto de la navegación. Las URLs que salen del sitio (canonical, `og:*`, links dentro del feed) son absolutas.
- **Páginas de error:** sin canonical ni tags sociales, pero con `<meta name="description">` del sitio.
- **`og:title`:**
  - En un post, el título solo, porque `og:site_name` ya lleva el nombre del blog.
  - En archivo, «Archivo»; en tema, «concurrencia — Archivo»; en la portada, el nombre del sitio.
  - Sumé `og:image:type`.
- **Textos en inglés** (la frase por defecto, las descripciones y el título del feed): son traducción mía. Revisalos.
- **README:**
  - Agregué `.env.example`: el README ya lo nombraba y no existía.
  - Saqué el badge de Alpine.js: el sitio no lo usa.

## 3. En qué se apartan las imágenes del diseño

Comparé por desplazamiento de cada elemento, a ¼ de píxel, contra capturas del prototipo en Chromium. Las capturas y las comparaciones están en la carpeta de abajo.

- **Vertical: igual.** Todo, anillo incluido, aparece 1 px corrido por igual, y eso viene del recorte de la captura (el marco del prototipo empieza en un y fraccionario).
- **Horizontal:**
  - Imagen de post: ±0,5 px.
  - Imagen por defecto: la primera línea de la frase se corre hasta 1,5 px hacia el final, y «IV» 1 px.
  - Los anchos de texto coinciden con los de Chromium a 0,1 px. La diferencia está en el rasterizado: FreeType contra Skia, y Chromium en Linux redondea la posición de algunos glifos.
- **Bordes de los glifos:** el suavizado no es idéntico. En la imagen de diferencia solo aparecen contornos.
- **Partido del título:** da los mismos cortes que `text-wrap: balance` de Chromium en los 7 títulos que comparé, con las fuentes del sitio.
  - La primera versión, con búsqueda del ancho mínimo, fallaba en el de 4 líneas.
  - La corregí al criterio de puntaje de Chromium (mínima suma de cuadrados del espacio sobrante).
- **Ícono de iOS:** idéntico al prototipo sin las esquinas, sin ningún píxel que difiera en más de 40.

**Qué se podría afinar:**

- El kerning depende de libraqm: sin `libfribidi` en el servidor, el texto sale sin kerning.
- Las fuentes de las imágenes tienen los mismos 512 caracteres que las del sitio. Un carácter fuera de latin y latin-ext (griego, emoji) sale como caja vacía. En la web, el navegador usaría otra fuente.
- El partido equilibrado puede dejar una palabra corta al final de línea («pingüinos y»). Chromium hace lo mismo.

**Imágenes para mirar:** `/home/ivanvallejos/Desktop/workbench/og-ventana-6/`.

| Archivo | Qué es |
| --- | --- |
| `01` | Post con título corto |
| `02` | El destacado |
| `03` | Título de 65 caracteres (64 px) |
| `04` | Post en inglés |
| `05` | Título de 100 caracteres |
| `06` | Tildes y «ñ» |
| `07`, `08` | Imágenes por defecto, ES y EN |
| `09` | Ícono de iOS |
| `10` | El post real |
| `proto-*` | Capturas del prototipo |
| `comparacion-*` | Prototipo arriba, la nuestra en el medio, la diferencia abajo |

## 4. Qué verifiqué, cómo, y qué quedó sin verificar

- **Pruebas:** `uv run python -m unittest`, 160 en verde.
- **Base local** (puerto 5435):
  - `BLOG_ALLOW_SEED=1 seed-dev`: 12 imágenes y las 2 por defecto.
  - `og-images` generó la del post real. Una segunda pasada dio «0 generadas, 12 sin cambios».
  - `og-images --force` regeneró las 13 después del cambio del partido.
- **Servidor** con `BLOG_BASE_URL=https://blog.ivanvallejos.dev` y el switch encendido, en el puerto 8012 (sigue levantado):
  - Con curl, las meta tags de portada, archivo, tema y post en los dos idiomas, y de la 404. La 404 no tiene canonical ni `og:`.
  - Las imágenes y el ícono responden 200 `image/png`.
- **Feeds**, con curl y parseados con ElementTree:
  - XML válido, `application/atom+xml` y la caché de 5 minutos.
  - 8 entradas en español y 5 en inglés, del más nuevo al más viejo.
  - Links absolutos, sin `headerlink`.
  - El único `http://` de todo el XML es el namespace de Atom.
  - En las páginas no queda ninguna URL `http://`. Las URLs relativas que quedan son la navegación interna, a propósito desde la ventana 4.
- **Playwright** sobre el Chromium del sistema:
  - Las 65 comprobaciones de la ventana 3, las 46 de la 4 y las 51 de la 5 pasan, contra servidores nuevos en 8020 y 8021.
  - Los errores de consola son los 404 que provocan las mismas pruebas.
  - Los puertos 8010 y 8011 los ocupan dos uvicorn de una sesión anterior (pids 3844922 y 3844923, de las 10:39), con el código viejo. No los toqué.
- **`sync --force` real: no terminó.**
  - En Notion, el post publicado «Levantar un servidor sin mirar» no tiene `Fecha Publicacion`, y `notion/client.py · get_details_from_post` falla con `TypeError`. El fallo es anterior a esta ventana.
  - Se corta antes del commit, así que la base quedó igual.
  - No lo arreglé porque cambia el comportamiento del sync. Las dos salidas posibles: cargar la fecha en Notion, o que el sync saltee ese post como al que le falta tema.
  - La imagen del post real («Parte del Proceso») la generó `og-images`. Después volví a correr `seed-dev`.
- **Sin verificar:**
  - Las tarjetas reales en LinkedIn, X y Facebook (el sitio no está desplegado).
  - El validador de feeds de W3C y un lector de feeds real.
  - Que el servidor tenga libraqm.
  - Cloudflare con el `?v=`.
  - El ícono en un iPhone.
  - El borrado de la imagen de un post real con el Notion real (está cubierto con el sync simulado).

## 5. Qué queda pendiente en todo el rediseño

**Antes de desplegar**

- **El post sin fecha en Notion** (ver §4). Corta el sync en producción igual que acá.
- **Orden de merge:** `idioma` y `opengraph` no están en `main`, y `opengraph` contiene a `idioma`.
- **Nombres de tema en inglés:** `TOPIC_NAMES` no tiene `presentacion` ni ningún tema nuevo, que salen con su nombre en español.
- **Revisar los textos en inglés** de esta ventana.
- **Pasos a mano:** `docs/despliegue-broadsheet.md`.

**Sin verificar en ninguna ventana**

- **Lector de pantalla real:** switch, combobox de búsqueda, región viva y panel.
- **Navegadores:** ninguno que no sea Chromium.
- **Safari de iOS:**
  - Bloqueo de scroll con `overflow: hidden`.
  - Margen con notch.
  - Teclado virtual con la barra sticky.
- **Compartir:**
  - `navigator.share` real.
  - La copia de respaldo con `execCommand` sin HTTPS.
  - Las páginas de LinkedIn y X.
- **Artículo:**
  - El índice con `pointer: coarse` en desktop.
  - El «18» que puede verse un instante en el lateral.
  - La captura visual del estado de carga.
  - El footer mobile del prototipo.
  - El foco con teclado recorrido a mano.
- **Servidor:**
  - El corte de servidor y la base caída de verdad.
  - El 500 detrás del proxy real.
- **Idioma:**
  - `hreflang` en Search Console.
  - Un post en inglés que venga de Notion.

**Sin resolver (técnico)**

- **Logs y base:**
  - Las excepciones no controladas dejan dos trazas en el log.
  - Hay que revisar que gunicorn reciba el logger `blog.errors`.
  - No hay timeout de conexión de psycopg2: con la base colgada, la 404 espera.
- **`Post.summary`** se calcula en cada lectura. Conviene una columna a partir de unos 300 posts.
- **Menciones a páginas de Notion:** se descartan. Podrían ser links a posts del blog.
- **Tokens duplicados:** los de las imágenes viven en `app/og/tokens.py`. Si cambia el CSS, hay que cambiarlos a mano.
- **Fuera de alcance, para más adelante:**
  - El vínculo entre un post y su traducción (`translation_of`).
  - La redirección por idioma.
  - Las imágenes dentro de los posts.
  - La lista aparte de ajustes visuales.
