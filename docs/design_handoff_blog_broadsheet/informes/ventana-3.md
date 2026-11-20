# Ventana 3 · Artículo y conversor de Notion — informe de cierre

La página de artículo y el conversor ampliado están en la rama `broadsheet`, en 12 commits, sin push ni merge. Contra el prototipo, a 390 y a 1280 px, la cabecera, el lateral, los botones y el panel quedan a ±0,1 px; la prosa coincide estilo por estilo con `PostBody.dc.html`. Las 57 pruebas del conversor y las 65 comprobaciones con Playwright pasan.

## 1. Qué quedó hecho, por archivo

- **`app/config.py`, `app/database.py`**: el `echo` del engine sale de `BLOG_SQL_ECHO`, apagado por defecto.
- **`app/routers/blog.py`**:
  - Los filtros del archivo son solo los temas con posts. Un tema vacío ya no se suma con «0»; su URL sigue respondiendo con el estado vacío y sin filtro marcado.
  - El post recibe `next_post`, `share_url` y `text_size` (`TEXT_SIZE`: 15–24, 18 por defecto, clave `blog.textSize`).
- **`app/selectors.py`**: `get_next_post(db, post)`, el post publicado inmediatamente antes (desempata por id).
- **`app/render.py`**:
  - Suma la extensión `sane_lists`: una lista con viñetas seguida de una numerada son dos listas.
  - `content_toc` guarda el texto sin escapar. Antes «&» llegaba como `&amp;` y el template lo escapaba otra vez.
  - Nuevo `markdown_to_text()`.
- **`app/models/post.py`**: `summary` recorta sobre el texto plano del primer párrafo. Con el formato en línea, la portada habría mostrado `<strong>` o `\*`, y un párrafo que empezaba en negrita se saltaba.
- **`notion/converter.py`** (reescrito):
  - Formato en línea: negrita, itálica, tachado, código y links.
  - Escapado de los caracteres que interpretan markdown y HTML.
  - Bloques: cita (con hijos), las dos listas (anidadas), separador, y `heading_1` como h2.
  - Mapeo de lenguajes validado contra Pygments, con «text» de respaldo.
  - Conteo de lo que no convierte.
  - API: `convert_blocks()`, que devuelve `Conversion(markdown, unsupported)`. `blocks_to_markdown()` queda como atajo.
- **`notion/client.py`**: `get_page_blocks` sigue el cursor hasta el final y carga los hijos de los tipos que el conversor anida.
- **`sync/services.py`, `cli.py`**:
  - `sync --force` reconvierte todos los posts.
  - `sync_posts` devuelve un `SyncReport`. La CLI imprime el resumen y, por post, los tipos no soportados, que además se registran con `logging.warning`.
- **`tests/test_converter.py`**: 57 casos con `unittest`, alimentados con bloques escritos a mano. Cubren cada tipo de bloque, los 72 lenguajes de Notion, formato combinado, anidación, escapado y tipos no soportados.
- **`app/seed.py`**:
  - El destacado se arma con bloques de Notion pasados por el conversor. Sigue la muestra de `PostBody` y suma la cita, las dos listas, una anidada, formato en línea, un link, tachado, un separador y texto que se escapa.
  - Nuevo tema vacío: `herramientas`.
- **`app/i18n.py`**: 11 claves nuevas en ES y EN para tamaño, compartir, avisos y cerrar el panel.
- **`app/templates/post.html`**:
  - Header de artículo, cabecera, prosa y «Siguiente».
  - Un solo `<aside id="reader">` que en mobile es el panel inferior y en desktop el lateral.
  - Botón flotante y velo.
  - Script en línea en el `<head>` que aplica el tamaño antes del primer pintado y marca `<html>` con `.has-js`.
- **`static/css/blog.css`**: secciones Artículo, Prosa y Controles de lectura, más las utilidades `.js-only` y `[hidden]`.
- **`static/css/blog-tokens.css`**: las medidas del artículo, el panel y el botón flotante, en el bloque marcado.
- **`static/css/pygments-light.css`**: medidas en `em` (ver §2).
- **`static/js/article.js`**: tamaño de texto, copiar, menú nativo y panel inferior (velo, tirador, Esc, foco atrapado y devuelto, scroll bloqueado).

## 2. Dónde me aparté del README o de CORRECCIONES, y por qué

- **Compartir en desktop:** Copiar · LinkedIn · X, como el prototipo D2 (lo decidiste vos al arrancar). El menú nativo va solo en mobile y no se muestra si no existe `navigator.share`.
- **Código en `em`.** El README fija 13 px para el bloque. El brief pide que todo escale con el tamaño elegido.
  - A 18 px da exactamente 13 px, 16×18 de padding y 1×5 en el código en línea.
  - Para eso edité `pygments-light.css`, que es una copia del handoff.
  - También corregí su margen inferior: el handoff daba 23,4 px y `PostBody` usa 16,9 px (1,3em de los 13 px).
- **Autor 16 px y «Siguiente» 26 px en desktop**, como el prototipo D2. El README dice 15 y 22, que son los valores de mobile. Interpolan entre los dos anchos.
- **Header de desktop:** igual que en el archivo (marca, Archivo, Buscar, ivanvallejos.dev ↗), pero sin ningún ítem marcado. En mobile, la flecha atrás lleva a la portada, como en el archivo.
- **Cerrar el panel:** el diseño no trae un botón. El tirador es un `<button>` «Cerrar opciones de lectura» con área de 44 px, sin cambio visible.
- **Tamaño en los extremos:** los botones quedan con `aria-disabled`, no `disabled`. Un botón deshabilitado pierde el foco, y dentro del panel el foco se perdería.
  - Cuando vuelve a 18, se borra la clave de `localStorage`.
- **Orden de los bloques.** El marcado sigue el orden de desktop (índice, tamaño, compartir). En el panel, CSS lleva el índice al final.
  - El Tab dentro del panel sigue el orden visual, que resuelve `article.js`.
  - El recorrido de un lector de pantalla sigue el marcado, con el índice primero.
- **Índice desde el panel:** cierra el panel y el foco sigue en la sección, no vuelve al botón flotante.
- **Áreas táctiles del índice en desktop:** cada link ocupa todo el paso (31 px por 220 px). Para llegar a 44 habría que cambiar el espaciado del diseño, así que solo crecen con `pointer: coarse`. Los botones de tamaño y compartir llegan a 44 con `.hit`.
- **Toast:** dice «Link copiado» (clave nueva `link_copied`). El botón usa «Copiado», que ya existía en el diccionario: el informe de la ventana 2 decía que faltaba.
- **Estilos que el README no define:**
  - h3: 1,1em, con margen 1,6em 0 0,45em.
  - Listas: sangría de 1,3em, 0,35em entre ítems, viñetas en neutral-700 y números tabulares.
  - Negrita: 600, el máximo de la fuente alojada.
  - Tachado: neutral-700.
  - Links: accent-700, subrayado de 0,06em.
  - Separador: la regla `.hr` de Broadsheet, con 2em de aire.
  - Ancla «#» de los títulos: neutral-600, visible al pasar el mouse o con foco.
  - Itálica dentro de una cita: se invierte a romana.
- **Conversor:**
  - El formato se emite como HTML en línea (`<strong>`, `<em>`, `<del>`, `<code>`, `<a>`), no como `**` o `~~`. Los marcadores de markdown dependen de los espacios que los rodean, y Notion parte los fragmentos en cualquier lugar.
  - Python-Markdown no trae extensión de tachado.
  - Los links a páginas de Notion, y los esquemas que no son http(s) o mailto, se descartan: queda el texto y se informa.
  - Los hijos de un título desplegable o de un párrafo con sangría van después del bloque, al mismo nivel.
  - Un ítem de lista con hijos que no son una sublista sale como lista «suelta» (`<li><p>`). CSS lo hace ver igual a una compacta.
- **Aviso de no soportados:** se muestra en la salida de `sync` y en el log, no en la tabla `sync_errors`. Si no, se repetiría en cada sync.

## 3. Qué descubrí que afecta a las ventanas siguientes

- **`.has-js` solo lo pone `post.html`.** La búsqueda (ventana 4) va a necesitar lo mismo: el botón de búsqueda se ve aunque no haya JavaScript. Conviene mover ese script en línea a `base.html`.
- **`[hidden] { display: none !important }`** ahora rige en todo el sitio.
- **`get_posts` tampoco pagina:** la consulta de la base de Notion trae 100 posts como máximo. Queda fuera del alcance de esta ventana.
- **`permalink_title` está fijo en español** en `render.py` y queda guardado dentro de `content_html`. El nombre accesible del ancla es «#». La ventana de idioma tiene que resolverlo al renderizar.
- **Compartir en LinkedIn y X** no va a mostrar una tarjeta con imagen hasta que existan las meta tags de OpenGraph (ventana 6).
- **`share_url` y todos los links de `post_url`** son absolutos (por `url_for`). Detrás del proxy salen con http si uvicorn no confía en sus cabeceras (ver §6).
- **`Post.summary`** ahora renderiza markdown en cada lectura. Es barato con pocos posts, pero `/search.json` lo va a llamar para cada post: si crece, cachearlo.
- **Las menciones a páginas de Notion** se podrían convertir en links a posts del blog, buscando el `notion_id`. Hoy se descartan.
- **Después de un `sync` hay que volver a correr `seed-dev`.** La base local queda con el post real, los 7 de muestra y cuatro temas sin posts (`web`, `test`, `nueva-pagina`, `herramientas`).

## 4. Qué verifiqué, cómo, y qué quedó sin verificar

- **Pruebas:** `uv run python -m unittest`, 57 en verde.
- **Rutas, con curl:**
  - Portada, archivo, temas, el tema vacío (`/herramientas/`, `/web/`) y los posts responden 200.
  - `/no-existe/` y un post inexistente responden 404.
  - El log no muestra errores ni 404 de estáticos. El SQL ya no aparece.
- **Comparación con el prototipo,** con capturas headless a 390×844 y 1280×800, por imagen y midiendo cada elemento:
  - Desktop: tag, metadatos, H1, autor, lateral, links del índice, botones de tamaño (54,4 y 59,4 px) e íconos de compartir (36 px), todo a ±0,1 px.
  - Mobile: header, cabecera y botón flotante iguales, contando el borde de 10 px y la barra de estado del marco.
  - Panel: mismas posiciones. Hay dos diferencias, las dos esperadas. Todo queda 46 px más alto, porque los posts de muestra tienen un cuarto h2. Y «Copiar» y «LinkedIn» son más anchos, porque Chromium en Linux no tiene `navigator.share` y el botón «⋯» no aparece.
  - Prosa contra `PostBody`: párrafo, h2, cita, código en línea, itálica y bloque de código idénticos en tamaño, interlineado, márgenes y padding.
- **Playwright sobre el Chromium del sistema (65 comprobaciones):**
  - Tamaño: cambiar, recargar y confirmar que la prosa ya está en 20 px cuando se inserta. El layout shift fue 0.
  - Extremos de 15 y 24: el botón queda con `aria-disabled` y el foco no se pierde.
  - Panel:
    - Se abre con toque. Lo cierran el velo, el tirador y Esc.
    - Mientras está abierto tiene `role="dialog"` y `aria-modal`, y el fondo no scrollea.
    - Con Tab, el foco no sale del panel y sigue el orden visual. Al cerrar vuelve al botón.
  - Copiar: muestra «Copiado» con su ícono, el toast «Link copiado» y el portapapeles queda con la URL. A los 1,6 s vuelve a «Copiar».
  - Índice: cierra el panel y deja la sección a 24 px del borde.
  - Lateral sticky a 24 px en desktop. Al pasar a desktop con el panel abierto, se cierra.
  - A 15 y 24 px, en los dos anchos: sin scroll horizontal, y el código scrollea dentro de su caja.
  - Con `prefers-reduced-motion`, el panel no tiene transición.
  - Sin JavaScript: en mobile no aparece ningún control; en desktop quedan solo el índice, LinkedIn y X.
  - Cero errores de consola y cero pedidos fallidos.
- **`sync --force` real:**
  - 1 post reconvertido («Parte del Proceso»), sin tipos no soportados.
  - Sus tres separadores, que antes se descartaban, ahora se ven.
  - No tiene h2, así que no muestra el índice. Es el único post real, así que tampoco tiene «Siguiente».
  - Después volví a correr `seed-dev`.
- **Sin verificar:**
  - `navigator.share` real (no existe en Chromium para Linux).
  - Safari de iOS: el bloqueo de scroll con `overflow: hidden` y el margen inferior en equipos con notch.
  - Lector de pantalla real.
  - Navegadores que no sean Chromium.
  - Las páginas de LinkedIn y X, que no abrí.
  - La copia de respaldo (`execCommand`) en un contexto sin HTTPS.
  - El índice con `pointer: coarse` en el layout de desktop.
  - El número del lateral puede mostrar «18» un instante antes de que corra `article.js`, si el tamaño guardado es otro. La prosa no salta.

## 5. Qué quedó disponible

- **Contexto del post:** `next_post`, `share_url` y `text_size`.
- **Selector:** `get_next_post(db, post)`.
- **Render:** `markdown_to_text(md)`.
- **Conversor:** `convert_blocks(blocks)` → `Conversion(markdown, unsupported: Counter)`, `blocks_to_markdown`, `code_language(name)`, `escape_text(text)` y `CHILD_TYPES`.
- **Cliente:** `get_page_blocks(id)` devuelve el árbol, con los hijos en la clave `children`.
- **Sync:** `sync_posts(db, force=False)` → `SyncReport(created, updated, deleted, skipped, unsupported)`.
- **Clases:**
  - `.js-only` (con `html.has-js`) y `[hidden]`.
  - Artículo: `.article`, `.article__main`, `.article__meta`, `.article__tag`, `.article__title`, `.article__author`, `.article__next` (con `-label` y `-link`).
  - Prosa: `.post-content`.
  - Controles: `.reader` (con `.is-open`), `.reader__handle`, `.reader__block` (con `--toc`, `--size`, `--share`), `.reader__label`, `.reader-toc__link`, `.reader-size__*`, `.reader-share__*`, `.reader-fab`, `.reader-veil` y `html.reader-open`.
- **Tokens:** `--article-*`, `--reader-*`, `--sheet-*`, `--fab-*`, `--veil-mix` y `--anchor-offset`.
- **JavaScript (`article.js`, sin API global):** se engancha por atributos.
  - Panel: `[data-reader-open]`, `[data-reader-close]`, `[data-reader-veil]` y `[data-reader-toc]`.
  - Tamaño: `[data-size-step]` y `[data-size-value]`.
  - Compartir: `[data-copy-link]`, `[data-copy-icon]`, `[data-copy-text]` y `[data-native-share]`.
  - Lee sus textos y límites de los `data-*` de `#reader`.
- **Seed:** `EMPTY_TOPICS` y `FEATURED_BLOCKS`, con los ayudantes `_rt()` y `_block()`.
- **Pruebas:** las fábricas `text()` y `block()` en `tests/test_converter.py`.

## 6. Pasos a mano en el servidor al desplegar

1. No hay migraciones ni dependencias nuevas.
2. Correr una vez `uv run python cli.py sync --force`, para reconvertir los posts existentes con el conversor nuevo, y revisar qué tipos no soportados informa.
3. El log de SQL queda apagado. Si allá se quiere verlo, definir `BLOG_SQL_ECHO=1`.
4. Revisar que uvicorn o gunicorn corran con `--proxy-headers` y `--forwarded-allow-ips` para la IP del proxy. Si no, `share_url` y los links del sitio salen con http.
5. Purgar en Cloudflare la caché de `blog.css`, `blog-tokens.css` y `pygments-light.css`. Los estáticos no llevan versión en la URL. `article.js` es nuevo.
