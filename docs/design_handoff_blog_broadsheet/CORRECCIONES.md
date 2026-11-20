# Correcciones al handoff de Broadsheet

Leer **antes** que `README.md` de esta carpeta. El README se escribió contra el estado del repo de julio 2026 (CIMIENTO v2: oscuro, Geist, ámbar, módulos fantasma). El repo cambió después. Donde esta nota y el README se contradicen, **gana esta nota**. En todo lo visual (medidas, colores, tipografía, textos) sigue mandando el README.

Estado verificado sobre `main` en el commit `3f3756b` (19 nov 2026).

## 1. Qué hay hoy en el repo

Un sistema intermedio que el README no conoce: oscuro, Newsreader para lectura, rail lateral con tags y fechas, barra de progreso de lectura. Se reemplaza entero por Broadsheet.

**Ya no existen** (el README pide borrarlos; ignorar): `partials/ghost_field.html`, `_light-palette.reference.css`, `Geist-Variable.woff2`, el header "warm" del post, la banda de lectura y el gradiente de fondo.

**Lo que hay que borrar en realidad:**

- `static/css/tokens.css` (tokens del sistema intermedio) y `static/css/pygments.css`.
- `static/fonts/Newsreader-Variable.woff2` y `Newsreader-Italic-Variable.woff2`.
- `static/js/article.js` (barra de progreso y sección activa del rail).
- `app/templates/partials/rail_listing.html` y `partials/tags_row.html`.
- En `base.html`: el rail, el bloque de la barra de progreso mobile y el preload de `Geist-Variable.woff2` (apunta a un archivo que ya no existe).
- En `fonts.css`: los `@font-face` de Geist y de Newsreader.

**HTMX no está cargado.** No hay `<script>` de HTMX ni atributos `hx-` en ningún template. Donde el README dice "el patrón actual" de filtros con HTMX, leer "el patrón a implementar".

## 2. Qué se conserva

- **`content_toc`** (columna JSONB en `Post`) y `render_markdown` en `app/render.py`: lista plana `[{level, id, text}]` de los h2/h3. Alimenta el bloque «En este artículo». No recalcular los títulos en el cliente.
- **`Post.summary`**: bajada derivada del primer párrafo. Es el respaldo de la bajada mientras no exista la propiedad `Resumen` de Notion. Ajustar el recorte a 160 caracteres, como pide el README.
- **`Post.reading_minutes`** y el flag **`featured`** con su orden `featured DESC, published_at DESC`.
- **`get_tag_counts`** en `app/selectors.py`: temas con su cantidad de posts. Sirve para los filtros del archivo y los bloques por tema de la portada.
- **`app/dates.py`**: base de los filtros de fecha. Hoy solo tiene meses en inglés.
- **Anclas de heading** (extensión `toc` con `permalink`).

## 3. Problemas del paquete de diseño

- **`static/public/favicon.svg` está roto.** Los tres trazos vienen sin color y falta el bloque `<style>` con la variante para pestañas oscuras; además trae un bloque `<metadata>` de 8 KB. **No copiarlo.** Reescribirlo: los tres `path` del favicon actual del repo, `stroke-width="3.6"`, `stroke-linecap="round"`, color `oklch(0.68 0.15 66)` y `oklch(0.80 0.13 72)` bajo `@media (prefers-color-scheme: dark)`, sin metadata.
- **`broadsheet.css` importa Source Serif 4 desde Google Fonts.** Se aloja en el repo (ver decisiones). Quitar esa línea `@import` es la **única** edición permitida a ese archivo.
- **Archivos `design/*.dc.html`**: son prototipos con estilos en línea y un runtime propio (`support.js`). Sirven para mirar y medir, no para copiar markup.

## 4. Decisiones cerradas (19 nov 2026)

- **Rama de trabajo:** `broadsheet`. Nada va a `main` hasta el cierre. Sin push ni deploy desde las ventanas.
- **Ventanas en secuencia**, no en paralelo: todas tocan `base.html` y `blog.css`.
- **Idioma al final.** Hasta esa ventana el blog es solo español. Pero desde la primera ventana **todo texto de interfaz sale de un diccionario por idioma** y los filtros de fecha reciben el idioma, para no rehacer templates después.
- **Switch ES/EN:** se maqueta y estiliza en la ventana de base, pero queda apagado por un flag de configuración hasta la ventana de idioma. No se muestra un control que no hace nada.
- **Conversor de Notion:** se amplía en la ventana del artículo (citas, listas, negrita, itálica, links, código en línea). Hoy solo emite h2, h3, párrafo y bloque de código.
- **Source Serif 4 alojada en el repo** (400, 600 e italic 400, subset latin + latin-ext), servida desde `/static/fonts/` detrás del proxy de Cloudflare.
- **Sin dependencias Python nuevas** salvo que la ventana lo justifique en su informe y quede aprobado.

## 5. Orden de ventanas

1. **Base:** CSS nuevo, `base.html` (header, footer, favicon), HTMX, borrado del sistema intermedio, diccionario de textos, fechas por idioma, ADR.
2. **Portada y archivo:** destacado, recientes, bloques por tema, ruta del archivo, filtros con HTMX, estados de carga y de lista vacía, toasts.
3. **Artículo:** prosa, código en tema claro, botón flotante y panel inferior en mobile, columna lateral en desktop, tamaño de texto, compartir, post siguiente, conversor de Notion.
4. **Búsqueda y errores:** `/search.json`, pantalla completa en mobile, diálogo ⌘K, 404 y 500.
5. **Idioma:** columna `lang`, propiedades nuevas de Notion, rutas `/en/`, switch, traducción de nombres de tema (el diseño no la modela: definirla ahí).
6. **OpenGraph:** meta tags, imágenes por post y por defecto, `apple-touch-icon`.

## 6. Pendientes conocidos fuera del diseño

- `notion/client.py · get_page_blocks` no pagina: un post de más de 100 bloques llega cortado. Resolver junto con el conversor.
- El orden de rutas: `/{category_slug}/` captura cualquier ruta fija de un segmento. Cada ruta fija nueva (`/archivo/`, `/search.json`, `/en/`) se registra antes.
