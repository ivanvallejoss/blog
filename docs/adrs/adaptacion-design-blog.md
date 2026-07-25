# Sistema de Diseño — Adaptación Blog (Informe Final)

**Sesión:** Rediseño visual de blog.ivanvallejos.dev + checks
**Fecha de cierre:** 2026-07-25
**Sistema de referencia:** CIMIENTO v2 (fuente de verdad: repo de la landing, `ivanvallejos.dev`)
**Regla de sincronización:** `tokens.css` y `fonts.css` son copias verbatim de la landing. Si divergen, **gana la landing**. Las extensiones del blog viven únicamente en `blog.css`, en bloque marcado.

---

## 1. Copiado verbatim vs. extensión

**Verbatim desde la landing:**

- `static/css/tokens.css`
- `static/css/fonts.css`
- `static/fonts/Geist-Variable.woff2`
- `static/fonts/GeistMono-Variable.woff2`

**Extensiones del blog** (bloque marcado al inicio de `blog.css` — únicos tokens no canónicos):

- `--measure: 700px` — medida de la columna de lectura.
- Familia `--code-*` para el tema Pygments: `--code-base`, `--code-comment`, `--code-kw`, `--code-lit`, `--code-fn`, `--code-punct`.
- **Único color nuevo de todo el blog:** `--code-lit: oklch(0.75 0.08 70)` — ámbar desaturado para literales, mismo hue 70 que el `--amber` canónico.

---

## 2. Decisiones de diseño tomadas

### Prosa (contexto de lectura larga)

- Columna editorial de 700px (`--measure`), centrada.
- Cuerpo: Geist 17px / interlineado **1.75** en `--ink-2` (jerarquía por valor: `--ink` reservado para titulares y `strong`).
- Titulares: `--font-display` (Geist Mono — decisión de identidad 2026-07-24, heredada de la landing). H1 con `clamp(30px, 5vw, 40px)`.

### Código

- Tema Pygments propio contra la paleta: keywords en ámbar, literales en `--code-lit`, definiciones en `--ink` peso 500, comentarios `--ink-5`, puntuación `--ink-4`.
- **Sin verde** (regla del token: verde solo estados vivos; en código estático no los hay). **Sin rojo** (el sistema no lo tiene; `.err` cae a base).
- Highlighting 100% server-side (python-markdown + codehilite). Contenedor `.codehilite` sobre `--mod-deep`, radio 3px (lenguaje de módulo).

### Dark-only

- Toggle de tema eliminado (decisión 2026-07-25); con él se fueron Alpine, el IIFE anti-flash y las hojas Pygments por tema.
- Paleta light v1 preservada en `static/css/_light-palette.reference.css` (**no linkeado**), como insumo para una futura versión light del sistema. Nota registrada: un light futuro se deriva de los tokens canónicos, no retoma esos valores.

### Índice y categoría

- Módulos quietos con el lenguaje k/v/d de `.blog-mod`/`.bio-mod` de la landing, sin animación de pulso.
- El módulo **warm significa "featured"**, con fallback al post más reciente si no hay ninguno destacado.
- Chips de categoría con lenguaje `.chip`/`.chip.hot`.

### Vista de post — banda de lectura

- Columna sólida `--bg-solid` con bordes laterales `--line` sobre el gradiente del sitio (clase `page-post`; body flex de altura completa para que la banda llegue al piso).
- Header de post como **gran módulo warm** (lenguaje `.profile-main`), en **breakout** ≥940px: se ensancha hasta 880px, rompiendo la banda.
- Composición en tres capas: fondo con fantasmas → banda de lectura → módulo del título sobre ambas.
- Pie de post con retorno: "← Todos los posts".

### Módulos fantasma

- 12 módulos estáticos (g1–g12) en índice, categoría y post; solo visibles ≥1180px; tonos `--mod-neutral` / `--mod-warm` / `--mod-slate` / `--mod-deep`; `position: fixed`, `pointer-events: none`, `aria-hidden`.

### Marca — anillo-ensamblaje

- Anillo de 3 segmentos (74° c/u, gaps de 24°), 3/4 de circunferencia, cuarto vacío abajo-derecha, **estático**, ámbar canónico.
- Usos: favicon (`static/public/favicon.svg`) y nav junto a `IV./blog` (SVG inline, 18px).
- **Candidato a reutilizarse en la landing** cuando el hero migre a foto (versión small-scale de la marca del hero).
- El punto del logo (`<span class="dot">.</span>` en `base.html`) coexiste con el anillo; recomendación registrada: anillo O punto, no ambos.

### Anclas y reading time

- Extensión `toc` en `render.py`: permalink `#` visible en hover, slugify unificado con python-slugify (ids consistentes con los slugs de posts), `scroll-margin-top` por header sticky, `:target` en ámbar.
- `reading_minutes` como property del modelo: ~200 wpm sobre el markdown **excluyendo bloques de código**, mínimo 1. Visible en cards ("5 min") y header de post ("5 min de lectura").

---

## 3. Estado del repo del blog al cierre

**Frontend:** migración completa a CIMIENTO v2. Archivos del sistema: `tokens.css`, `fonts.css`, `blog.css`, `pygments.css`, `_light-palette.reference.css`, `favicon.svg`, fuentes variables. Templates: `base.html`, `index.html`, `category.html`, `post.html`, `partials/post_list.html`, `partials/ghost_field.html`.

**Backend tocado en fase de checks** (implementado por Ivan con specs de esta ventana, verificado funcionando):

- Flag `featured`: columna booleana con `server_default=false`, migración Alembic, comando CLI `feature <slug> [--off]` (múltiples featured permitidos), orden `featured DESC, published_at DESC` en selector de índice y en la relación `Category.posts`.
- Router de categoría sin branching HTMX: el server siempre devuelve la página completa y el cliente recorta con `hx-select="#listing"` (wrapper `#listing` en índice y categoría, header de categoría incluido en el swap).
- `render.py` con extensión `toc`; `backfill_db` como herramienta recurrente de re-render (ya no "one-time only").
- Property `reading_minutes` en `Post`.

**Eliminados del repo:** `main.css`, `pygments-dark.css`, `pygments-light.css`, `GeistSans-Regular.woff2`, `GeistMono-Regular.woff2`, `GeistMono-Bold.woff2`, toggle de tema y Alpine.

---

## 4. Deudas y registro para futuras ventanas

### Features pendientes (en orden de prioridad)

1. **RSS/Atom** — endpoint + armado del XML desde el selector del índice. Decisión pendiente: contenido completo vs. resumen en el feed. Doble uso: el feed es una API read-only de posts, consumible por la landing u otras piezas. *Ventana dedicada.*
2. **OpenGraph / meta description por post** — links que renderizan con título y descripción en LinkedIn/X. Doble uso directo con la búsqueda laboral. *Ventana dedicada.*
3. Menores: TOC visible en posts largos (`md.toc` ya disponible tras el cambio de render); estilo diferenciado del header de categoría si el warm resulta excesivo en ese contexto.

### Tensiones para la v2 del sistema de diseño (a trabajar de forma íntegra, no ahora)

a. Promover `--measure`, interlineado de prosa y la familia `--code-*` a `tokens.css` canónico como sección "contextos de lectura", una vez que landing y blog estén estables.
b. Ausencia de color de error/peligro. Decisión de **identidad** pendiente: ¿el rojo entra como tercer color (rompiendo "ámbar único color de marca + verde semántico") o el error se expresa en ámbar/intensidad? Dolerá cuando un post muestre diffs o warnings.
c. `--bg-solid` nació como "fondo de interludios/ticker" y el blog lo resignificó como "superficie de lectura". Formalizar roles de superficie (fondo / banda / módulo / lectura) y actualizar el comentario en `tokens.css`.

### Optimización condicionada a crecimiento

- El índice carga filas completas de `Post` (incluye `content_markdown` y `content_html`). A partir de ~100 posts: `load_only` de columnas livianas + `reading_minutes` promovido a columna calculada en sync.

---

*Este informe es el contexto de entrada para las ventanas de RSS, OpenGraph y la v2 del sistema de diseño. Registro compartido con la ventana orquestadora de la landing.*
