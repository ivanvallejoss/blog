# El blog pasa a Broadsheet

**Fecha:** 2026-11-19
**Estado:** aceptada
**Reemplaza:** `adaptacion-design-blog.md` (CIMIENTO v2) y el sistema intermedio que lo siguió. Ese ADR no se edita: queda como registro.
**Fuentes:** `docs/design_handoff_blog_broadsheet/README.md` (especificación) y `CORRECCIONES.md` (estado real del repo y decisiones cerradas).

---

## Contexto

El blog tuvo dos sistemas visuales antes de este:

1. **CIMIENTO v2** (julio 2026): oscuro, Geist y Geist Mono, ámbar como acento, módulos «fantasma», tokens copiados verbatim desde la landing.
2. **Un sistema intermedio oscuro**: Newsreader para la lectura, rail lateral con temas y fechas, barra de progreso de lectura. Nunca tuvo ADR propio.

Ninguno de los dos priorizaba la lectura en mobile, y el segundo cargaba piezas (rail, progreso, JS de sección activa) que no resolvían un problema real del lector.

## Decisión

El blog adopta **Broadsheet**: papel claro, todo el texto en Source Serif 4, cian (`--color-accent`) para lo interactivo y magenta (`--color-accent-2`) como segundo acento, de uso raro. Mobile primero, con la lectura como prioridad.

### Qué se reemplaza

- CIMIENTO v2 entero: `tokens.css`, la paleta oscura, Geist como fuente de texto, los módulos y el header «warm».
- El sistema intermedio: Newsreader, el rail, la barra de progreso y `article.js`.
- El tema de código oscuro (`pygments.css` → `pygments-light.css`).

### Qué se conserva de la identidad

- **El anillo ámbar**, solo como marca: header, favicon y, más adelante, la imagen OpenGraph. Mismos tres trazos de siempre. Anillo **o** punto, nunca los dos: el «.» junto a «IV» no vuelve.
- **Geist Mono**, solo para metadatos (fecha · tema · minutos), código y el `/blog` de la marca.

### La regla de tokens verbatim deja de valer

La regla de CIMIENTO («`tokens.css` y `fonts.css` son copias verbatim de la landing; si divergen, gana la landing») **deja de aplicar al blog**. El blog ya no se sincroniza con la landing.

La fuente de verdad pasa a ser:

- `static/css/broadsheet.css`: copia del design system Broadsheet. **No se edita.** La única diferencia con el original es que no tiene el `@import` de Google Fonts, porque la fuente se aloja en el repo.
- `static/css/blog-tokens.css`: extensiones del blog (mono, anillo, medida de lectura, `--code-*` y el bloque de layout). Es el único lugar para tokens nuevos.
- `static/css/blog.css`: solo clases que consumen esas variables. Sin colores, radios, sombras ni espaciados sueltos.

### Decisiones de implementación de la base

- **Source Serif 4 alojada** en `static/fonts/` (OFL): la romana es variable en peso 400–600 y conserva el eje óptico; la itálica queda fija en 400. Las dos están recortadas a latin + latin-ext. Se sirven detrás del proxy, sin depender de Google Fonts.
- **Textos de interfaz por idioma** desde el principio (`app/i18n.py`). El blog sigue siendo solo español hasta la ventana de idioma, pero ningún template tiene texto escrito a mano.
- **Switch ES/EN** maquetado pero apagado (`BLOG_LANG_SWITCH`): no se muestra un control que no hace nada.
- **HTMX 2.0.4** alojado en `static/js/`, cargado con `defer`.

## Consecuencias

- Las ventanas siguientes (portada y archivo, artículo, búsqueda y errores, idioma, OpenGraph) construyen sobre `base.html` y `blog.css`. Ver `CORRECCIONES.md` §5.
- Cambiar el aspecto del sistema se hace en el design system Broadsheet y se vuelve a copiar `broadsheet.css`, no editándolo en el repo.
- El ADR de CIMIENTO queda como histórico; sus reglas de sincronización con la landing ya no obligan.

---

## Estado final (20 nov 2026, ventana 6)

El rediseño quedó completo en seis ventanas, con un informe cada una en `docs/design_handoff_blog_broadsheet/informes/`. Todo está en la rama `opengraph`, que sale de `idioma`. `main` tiene hasta la ventana 4. Nada está desplegado: los pasos a mano están en `docs/despliegue-broadsheet.md`.

| Ventana | Qué dejó |
| --- | --- |
| 1 · Base | CSS de Broadsheet, `base.html`, header y footer, fuentes alojadas, diccionario de textos, fechas por idioma. |
| 2 · Portada y archivo | Destacado, recientes, bloques por tema, `/archivo/`, filtros con HTMX, carga y toasts, `seed-dev`. |
| 3 · Artículo | Prosa, código claro, panel de lectura y lateral, tamaño de texto, compartir, «Siguiente», conversor de Notion ampliado. |
| 4 · Búsqueda y errores | `/search.json`, búsqueda en pantalla completa y diálogo ⌘K, 404 y 500 con planchas. |
| 5 · Idioma | `Post.lang` y `Post.excerpt`, propiedades `Idioma` y `Resumen`, rutas `/en/`, switch, `hreflang`, nombres de tema traducidos. |
| 6 · OpenGraph y feed | Meta tags y canonical, imágenes para compartir, `apple-touch-icon`, feeds Atom. |

### Deudas del ADR de julio, resueltas

`adaptacion-design-blog.md` §4 dejó dos features pendientes. Las dos quedaron resueltas en la ventana 6:

1. **RSS/Atom:** está resuelta la decisión que había quedado abierta, contenido completo o resumen.
   - Hay un feed Atom por idioma, en `/rss.xml` y `/en/rss.xml`, con los últimos 20 posts completos. Lo arma `app/feed.py` y la ruta está en `app/routers/blog.py · rss`.
   - Atom en vez de RSS 2.0: tiene `<content type="html">`, ids permanentes y fechas RFC 3339.
   - Todas las páginas lo enlazan con `<link rel="alternate">` y el footer muestra «RSS».
2. **OpenGraph y meta description:**
   - `app/meta.py` arma descripción, canonical, OpenGraph y `twitter:card` para portada, archivo, tema y post, en los dos idiomas. Lo pinta `partials/meta.html`.
   - Cada post tiene su imagen de 1200 × 630, y cada idioma una por defecto. Las dibuja `app/og/` con Pillow, desde los mismos tokens y la misma Source Serif 4 en opsz 14.
   - Se generan en el sync y con `cli.py og-images`, solo cuando cambia lo que muestran. La huella va dentro del PNG y en el `?v=` de la URL.

### Decisiones de la ventana 6

- **Pillow** es la única dependencia nueva de todo el rediseño. El servidor no tiene navegador y no convierte SVG. Los TTF de las imágenes viven en `app/og/fonts/`, que no se sirve como estático.
- **Los tokens que usan las imágenes** están duplicados como constantes en `app/og/tokens.py`, cada una con el nombre de su variable de CSS. Si cambia un token del sitio, hay que cambiarlo ahí también.
- **Región de `og:locale`:** `es_AR` y `en_US`.
- **El `apple-touch-icon.png` se commitea.** Lo dibuja el mismo código del anillo (`cli.py touch-icon`).

## Apartamientos del diseño original (20 nov 2026, ventana 7)

Después de ver el rediseño funcionando se cambiaron cinco puntos del handoff a propósito. En todo lo demás el README del handoff sigue mandando. El detalle está en `informes/ventana-7.md`.

| Punto | Handoff | Ahora | Motivo |
| --- | --- | --- | --- |
| Separación entre secciones | Solo espacio, sin líneas | Además del espacio, una raya de 48 × 1 px en `--color-divider`, alineada a la izquierda sobre el rótulo (`.section-rule`). Va sobre Recientes, Por tema, cada año del archivo y «Siguiente». Nunca sobre la primera sección de la página, ni entre filas, ni en el lateral | Con solo espacio, las secciones se leían pegadas. La raya marca dónde empieza cada una sin cortar la página de lado a lado |
| Bloques por tema de la portada | `h3` con el nombre del tema en 22 px, igual que un título de post | Rótulo «Por tema» como «Recientes». Cada tema abre con la misma etiqueta de la cabecera del artículo (macro `topic_tag`) y su cantidad en mono. Los posts van en una lista compacta de 16 px | No se distinguía un bloque que organiza un tema de un post. Un tema se ve igual en todo el sitio |
| Lateral del artículo | 220 px, a 80 px de la prosa | 180 px, a 64 px | Lateral más liviano, que acompaña a la prosa más angosta. Los controles siguen entrando |
| Columna de lectura | 680 px (unas 81 letras por línea a 18 px) | 600 px (unas 72), en el único token `--measure` | Las líneas largas cansaban. Es un valor a probar: se cambia en un solo lugar |
| Índice del artículo | Lista de links estática | Marca la sección que se está leyendo: inactivas en neutral-700, la activa en el color del texto con una barrita de acento a la izquierda y `aria-current`. Sin JavaScript queda la lista de links | Muestra dónde está el lector en un post largo, en el lateral y en el panel de mobile |
