# Handoff: rediseño del blog en Broadsheet ("1a · Índice")

Repo destino: `ivanvallejoss/blog` (FastAPI + Jinja2 + HTMX, contenido desde Notion).
Este README es el contexto de entrada para la ventana de implementación. Debe bastar por sí solo.

---

## 1. Resumen

El blog pasa de **CIMIENTO v2** (oscuro, Geist/Geist Mono, ámbar) a **Broadsheet**: papel claro, todo en Source Serif 4, cian para lo interactivo y magenta como segundo acento, raro. Lo que queda de la identidad propia:

- **El anillo ámbar**, solo como marca: nav, favicon e imagen OpenGraph.
- **Geist Mono**, solo en metadatos (fecha · tema · minutos), en código y en el `/blog` del logo.

Objetivo: minimalismo práctico, pensado primero para mobile. La lectura es lo principal, con búsqueda rápida, tiempo de lectura, tamaño de texto ajustable, botón de compartir y switch ES/EN global.

## 2. Sobre los archivos de diseño

Lo que está en `design/` son **referencias de diseño hechas en HTML**: muestran el aspecto y el comportamiento esperados, **no son código de producción**. La tarea es **recrearlos con Jinja2 + CSS + HTMX dentro del repo**, siguiendo sus patrones (`base.html`, `partials/`, `blog.css`). Se abren directo en el navegador:

- `design/Blog 1a.dc.html`: portada, artículo, archivo y búsqueda, en mobile y desktop. El switch ES/EN, los filtros, la búsqueda y el tamaño de texto funcionan.
- `design/Blog 1a Extras.dc.html`: errores 404/500, imagen OpenGraph (opción **E2a**), estados y favicon.
- `design/PostBody.dc.html`: muestra de prosa (párrafo, h2, código, cita) en ES/EN.

Los estilos de estos archivos están escritos en línea solo porque así se hacen los prototipos. **En el repo van en clases de CSS.**

## 3. Fidelidad

**Alta fidelidad.** Los colores, la tipografía, el espaciado y los textos son finales. Recrear al píxel en el ancho de 390 px (mobile) y en 1280 px (desktop), con un layout fluido entre ambos.

---

## 4. Archivos de este paquete

```
static/css/broadsheet.css      ← copia verbatim del design system (tokens + clases .btn/.tag/.input/.cmyk-num…)
static/css/blog-tokens.css     ← extensiones del blog (mono, anillo, medida, --code-*), cargar después
static/css/pygments-light.css  ← reemplaza pygments.css (tema claro)
static/public/favicon.svg      ← favicon nuevo (con variante para pestañas oscuras)
design/…                       ← referencias HTML
```

Orden de carga en `base.html`:
```html
<link rel="preload" href="/static/fonts/GeistMono-Variable.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/static/css/fonts.css">          <!-- dejar SOLO el @font-face de Geist Mono -->
<link rel="stylesheet" href="/static/css/broadsheet.css">     <!-- trae Source Serif 4 desde Google Fonts -->
<link rel="stylesheet" href="/static/css/blog-tokens.css">
<link rel="stylesheet" href="/static/css/blog.css">           <!-- reescrito -->
<!-- post.html: pygments-light.css -->
<link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/duotone/style.css">
```
Opcional: alojar Source Serif 4 en el propio servidor (400, 600 e italic 400) y quitar el `@import` de Google Fonts de `broadsheet.css`.

**Eliminar del repo:** `tokens.css` (CIMIENTO), `Geist-Variable.woff2`, `pygments.css`, `partials/ghost_field.html` y sus includes, el header "warm" del post, la banda de lectura `page-post` y el gradiente de fondo. Conservar `_light-palette.reference.css` solo si se quiere como registro histórico.

**ADR:** registrar en `docs/adrs/` la decisión "CIMIENTO → Broadsheet en el blog". La regla de "tokens verbatim desde la landing" deja de valer para el blog.

---

## 5. Design tokens

Todos salen de `broadsheet.css`. Usar las variables, nunca los hex sueltos.

| Rol | Variable | Valor |
|---|---|---|
| Fondo | `--color-bg` | #f3f2f2 |
| Superficie (código, inputs, toasts) | `--color-surface` | #eae9e9 |
| Texto | `--color-text` | #201e1d |
| Texto secundario | `--color-neutral-800` | #444141 |
| Metadatos y etiquetas | `--color-neutral-700` | #605d5d |
| Inactivo (EN apagado, año grande) | `--color-neutral-600` | #7d7979 |
| Acento interactivo | `--color-accent` | #0088b0 (hover `-600` #1186ac, pressed `-700` #006786) |
| Links de texto | `--color-accent-700` | #006786 |
| Fondo de tag | `--color-accent-100` | #e9f8ff (texto `-800` #004961) |
| «Destacado» y alertas | `--color-accent-2-700` | #aa0b56 |
| Anillo (nav / OG) | `--brand-ring` | oklch(0.72 0.15 68) |
| Anillo (favicon) | `--brand-ring-small` | oklch(0.68 0.15 66) |
| Velo de fondo (sheet/modal) | — | `color-mix(in srgb, var(--color-neutral-900) 40%, transparent)` (45 % en ⌘K) |

Radios: `--radius-sm` 1px, `--radius-md` 2px, `--radius-lg` 4px. El sheet usa 18px arriba y los toasts `--radius-lg`.
Sombras: `--shadow-sm/md/lg`. El FAB usa `md`; el sheet, el diálogo ⌘K y los toasts usan `lg`.
Espaciado: `--space-1…8` = 5/10/15/20/30/40px. Entre secciones: **56px en mobile y 112px en desktop**, solo espacio, sin líneas.

**Tipografía**
- Serif: `var(--font-heading)` / `var(--font-body)` = Source Serif 4. Peso de títulos 600, cuerpo 400, italic real.
- Mono: `var(--font-mono)` = Geist Mono. Clase `.meta-mono`: 11.5px, uppercase, +0.04em, `--color-neutral-700` (en desktop, 12px).

| Elemento | Mobile | Desktop |
|---|---|---|
| H1 del destacado (portada) | 34px / 1.1 | 58px / 1.04 |
| Bajada del destacado | 17px, neutral-800 | 21px / 1.5, máx. 580px |
| Kicker «Destacado» | 12px, uppercase, +0.1em, accent-2-700 | 13px |
| H1 del post | 32px / 1.12 | 48px / 1.08 |
| Título de fila (lista) | 20px / 1.2, peso 600 | 19px / 1.25 |
| Título de fila (archivo) | 18px / 1.25 | 20px |
| H1 de página (Archivo) | 36px | 42px |
| Etiqueta de sección (`h6`) | 13px, uppercase, +0.08em, neutral-700 | igual |
| Cuerpo de la prosa | 18px / 1.7, neutral-900 (ajustable 15–24) | igual, columna de 680px |
| h2 de la prosa | 1.3em, margen 1.8em 0 .5em | igual |
| Cita | italic 1.15em / 1.5, neutral-800, **sin borde lateral** | igual |
| Código en bloque | Mono 13px / 1.6, fondo surface, padding 16×18, radio 2px | igual |

`text-wrap: balance` en los H1 y `pretty` en los párrafos.

---

## 6. Pantallas

### Header (todas las páginas)
- **Mobile:** fila de 44px de alto con padding `8px 12px 8px 20px`. A la izquierda, la marca: anillo SVG de 20px + «IV» serif 600 18px + «/blog» mono 14px neutral-700, con 8px de separación. A la derecha, el switch ES/EN y un `.btn.btn-icon` de 44×44 con lupa (Phosphor duotone `ph-magnifying-glass`, 22px).
- **En artículo y archivo** el header cambia: a la izquierda una flecha atrás (`ph-arrow-left`); en el artículo, el anillo solo al centro.
- **Desktop:** contenedor de 1120px de máximo, padding 28×40. Marca a la izquierda (anillo de 22px, 20px / 15px). Después, con 32px de separación: «Archivo», `.btn.btn-secondary` «Buscar ⌘K» (el ⌘K en mono 11px), el switch ES/EN y «ivanvallejos.dev ↗» con `white-space: nowrap`.
- **Switch ES/EN:** dos `<button>` en mono 12px separados por «/» en neutral-500. El idioma activo va en `--color-text` y el inactivo en `--color-neutral-600`. Cada botón ocupa 44px de alto en mobile.
- **SVG del anillo:** son los 3 paths del `favicon.svg` actual, con `stroke: var(--brand-ring)`, `stroke-width: 3` y `stroke-linecap: round`. **No** poner el punto «.» junto a «IV» (el ADR ya recomendaba anillo o punto, no ambos).

### M1 / D1 · Portada (`/`, `index.html`)
1. **Destacado:** `featured DESC, published_at DESC`, primer post. Kicker «Destacado», H1 con link al post, bajada (ver §8 Datos) y meta en mono «14 NOV · concurrencia · 12 min». En desktop se suma un `.btn.btn-primary` «Leer artículo».
2. **Recientes:** `h6` y una lista de filas. Cada fila es un `<a>` en bloque, con padding de 14px vertical y 6px entre el título y la meta en mono. **Sin bordes entre filas.**
3. **Mobile:** el `.btn.btn-ghost` «Ver archivo completo →» lleva al archivo.
4. **Desktop:** grilla de `7fr 4fr` con 96px de separación (el destacado a la izquierda, 4 recientes a la derecha). Debajo, a 112px, una grilla de 3 columnas con un bloque por tema: `h3` + cantidad en mono 13px + títulos de 17px.
5. **Footer:** 13px neutral-700: «© 2026 Iván Vallejos · RSS · ivanvallejos.dev ↗».

### M2 / D2 · Artículo (`/{cat}/{slug}/`, `post.html`)
- **Cabecera:** `.tag.tag-accent` con el tema + meta en mono «14 NOV 2026 · 12 min», H1 y «Iván Vallejos» (15px neutral-700). Después, `post.content_html` dentro de `.post-content`.
- **Pie:** «SIGUIENTE» en mono + título del post siguiente en 22px peso 600, color accent-700, con «→».
- **Mobile, botón flotante de lectura:** botón de 56px, círculo, fondo `--color-accent` y color `--color-bg`. Ícono `ph-text-aa` de 26px, posición absoluta a 20px de la derecha y 32px de abajo, `--shadow-md`. Hover `accent-600`, pressed `accent-700`. Al tocarlo abre un **panel inferior (bottom sheet)**:
  - Velo con 40 % de neutral-900; tocarlo cierra.
  - Panel con fondo `--color-bg`, radio de 18px arriba, padding `12px 24px 36px`, 22px entre bloques y un tirador de 40×4 en neutral-300.
  - «Tamaño de texto»: `[A−] 18 px [A+]` (`.btn-secondary` de 44px de alto; A− en 14px, A+ en 19px, valor en mono 13px). Rango 15–24, paso 1.
  - «Compartir»: `[Copiar] [LinkedIn] [⋯]`. «⋯» abre `navigator.share` si existe. «Copiar» muestra «Copiado» con el ícono `ph-check` durante 1.6 s y además el toast.
  - «En este artículo»: links a los h2 (TOC), en 17px accent-700 con 8px de padding vertical.
- **Desktop:** grilla de `220px minmax(0,680px)` con 80px de separación. Un `<aside>` sticky (top 24px) con «En este artículo», «Tamaño de texto» y «Compartir» (íconos de 36px). Sin botón flotante.

### M3 / D3 · Archivo (`/archivo/` o la portada con `?tema=`)
- Título «Archivo» y «7 posts · 3 temas».
- **Filtros por tema:** `Todo` + uno por tema, con la cantidad en mono 11px al 75 % de opacidad. El activo es `.btn-primary` y los demás `.btn-secondary`, 40px de alto, `white-space: nowrap`.
  - En mobile van en una fila con scroll horizontal.
  - En desktop van en una columna dentro del aside de 220px.
- **Lista agrupada por año:** `h6` con el año. Cada fila es una grilla de `60px 1fr`: fecha en mono «14 NOV» | título 18px/600, y debajo «TEMA · 12 min» en mono.
  - En desktop la grilla es de `72px 1fr 150px 56px`: fecha | título 20px | tema en mono | minutos alineados a la derecha.
- Filtrar con HTMX usando el patrón actual: `hx-get` a la URL del tema, `hx-target="#listing" hx-select="#listing" hx-swap="outerHTML" hx-push-url="true"`.
- **Rutas:** hoy `/{category_slug}/` choca con cualquier ruta fija (`/archivo/`, `/en/`, `/search.json`). Registrar las rutas fijas **antes** de la de categoría, o reservar esos slugs.

### M4 / D4 · Búsqueda
- **Mobile, pantalla completa:**
  - Arriba, un `.input` de 44px con la lupa adentro (padding-left 38px, 16px para que iOS no haga zoom) y un `.btn-ghost` «Cancelar».
  - Con la búsqueda vacía: «Temas» como `.tag.tag-accent` tocables (14px, padding 10×14); tocar uno lo usa como búsqueda.
  - Con texto: «N resultados» y una fila por post con título 19px, bajada 15px neutral-800 y meta en mono.
- **Desktop, diálogo ⌘K:** se abre con ⌘K/Ctrl+K o con el botón del header.
  - Velo al 45 %. Diálogo de 640px, a 96px del borde superior, fondo bg, `--radius-lg`, `--shadow-lg`.
  - Input de 48px en 18px. Resultados con un máximo de 440px de alto y scroll; el activo lleva fondo `accent-100`.
  - Pie con fondo surface en mono 11.5px: «↑↓ navegar · ↵ abrir · esc cerrar».
- **Motor:** del lado del cliente. Exponer `GET /search.json` con `[{title, slug, category, category_slug, excerpt, published_at, reading_minutes, lang}]`, cargarlo la primera vez que se abre la búsqueda y filtrar por `includes` sin distinguir mayúsculas ni tildes (NFD, quitando diacríticos) sobre título, tema y bajada. Con menos de 20 posts no hace falta índice.
- **Sin resultados:** título 26px «Nada sobre «{q}» todavía», «Probá con otra palabra o explorá por tema.», los tags de temas y «Sugerime un tema ↗» (link opcional).

---

## 7. Extras

### Errores (`errors/404.html`, `errors/error.html`)
- **Número:** construcción de planchas `.cmyk-num` (ya está en `broadsheet.css`), sin JS:
  ```html
  <div class="cmyk-num" style="font-size:132px;font-weight:600;letter-spacing:-.03em">
    <span class="paper">404</span><span class="plate plate-c" aria-hidden="true">404</span>
    <span class="plate plate-m" aria-hidden="true">404</span><span class="plate plate-y" aria-hidden="true">404</span>
  </div>
  ```
  132px en mobile y 220px en desktop. El H1 va 32px debajo (44px en desktop).
- **404:** «Página no encontrada» / `{{ detail or "El contenido que buscás no existe o fue movido." }}`, un input de búsqueda (en desktop, con `.btn-primary` «Buscar»), «Quizás buscabas» con 2–3 posts recientes y «Volver al inicio →».
- **500 y genérico:** «Algo salió mal» / «Error inesperado. Intentá de nuevo en unos segundos; si sigue pasando, avisame.», `.btn-primary` «Reintentar» (`location.reload()`) y `.btn-secondary` «Volver al inicio». Opcionalmente, una referencia del error en mono 11.5px.
- **Voseo:** se mantiene en los textos de error, como en las plantillas actuales.

### OpenGraph (opción elegida: E2a)
- **Imagen de post, 1200×630, fondo `--color-bg`, padding de 72px vertical y 80px horizontal:**
  - Arriba a la izquierda: anillo de 34px + «IV» 30px/600 + «/blog» mono 22px.
  - Pegado abajo: el tema en 22px, uppercase, +0.1em, accent-700; el título en 78px / 1.04, peso 600, -0.02em, máximo 960px de ancho y `balance` (si supera ~60 caracteres, bajarlo a 64px); y una fila en mono 22px con «Iván Vallejos · 14 nov 2026 · 12 min» a la izquierda y «blog.ivanvallejos.dev» a la derecha.
- **Imagen por defecto (portada y archivo):** anillo de 120px arriba a la izquierda. Abajo, «IV» en 110px + «/blog» en mono 56px y la frase de 36px «Notas de Iván Vallejos sobre *concurrencia*, sistemas de diseño y la vida alrededor del código.»
- **Generación:** en el sync (`cli.py sync`), solo cuando cambia el título, el tema o la fecha. Guardarla en `static/og/{slug}.png`. Hay dos opciones a decidir en la ventana:
  - (a) una plantilla Jinja `og.html` capturada con Playwright;
  - (b) un SVG compuesto y convertido a PNG con resvg/cairosvg (requiere las fuentes instaladas).
- **Meta tags en `base.html`:** un `{% block meta %}` con `og:title`, `og:description` (la bajada), `og:image`, `og:url`, `twitter:card=summary_large_image` y `<meta name="description">`.

### Estados
- **Carga con HTMX:** mientras se espera el swap, la lista actual baja al 40 % de opacidad (`.htmx-request #listing { opacity:.4 }`) y aparece una barra cian de 2px fija arriba de todo. El filtro activo muestra el ícono `ph-circle-notch` girando. **Sin skeletons.**
- **Tema vacío / sin posts en el idioma:** título 26px y texto 17px. Si existen posts en el otro idioma, «There are N posts on *life* in Spanish.» + `.btn-secondary` «Ver en español».
- **Toasts:**
  - Posición absoluta a 16px de los costados, por encima de la zona del pulgar (40px desde abajo; el segundo, apilado a 118px).
  - Fondo `--color-neutral-100`, `--shadow-lg`, `--radius-lg`, padding `6px 6px 6px 16px`, 15px.
  - Ícono de 20px: `ph-check-circle` en accent-700 para avisos de éxito y `ph-wifi-slash` en accent-2-700 para fallos.
  - Acción opcional como `.btn-ghost` («Reintentar»).
  - Se ocultan a los 3 s, salvo los de error con acción. Conectarlos a `htmx:responseError` y `htmx:sendError`.

### Favicon
- Usar `static/public/favicon.svg` (incluido): trazo de 3.6, ámbar `oklch(0.68 0.15 66)` y `oklch(0.80 0.13 72)` cuando `prefers-color-scheme: dark`.
- Agregar `apple-touch-icon.png` de 180×180: fondo `#f3f2f2`, anillo de 110px centrado y trazo de 2.8.
- `<link rel="icon" type="image/svg+xml" href="/static/public/favicon.svg">` + `<link rel="apple-touch-icon" href="/static/public/apple-touch-icon.png">`.

---

## 8. Datos, rutas y estado

**Modelo (`Post`)**
- `lang: str` con `'es' | 'en'`, por defecto `'es'`. Nueva propiedad `Idioma` (Select) en Notion. Agregar migración Alembic.
- `excerpt: str | None`: la bajada, desde una nueva propiedad `Resumen` en Notion. Si falta, usar el primer párrafo del markdown recortado a 160 caracteres. La usan la portada, la búsqueda y OpenGraph.
- `translation_of` (opcional, más adelante) para enlazar un mismo post en ES y EN.

**Rutas**
- `/` y `/en/`: portada por idioma.
- `/{cat}/` y `/en/{cat}/`: tema.
- `/{cat}/{slug}/` y `/en/{cat}/{slug}/`: post.
- `/archivo/` y `/en/archive/`: archivo.
- `/search.json?lang=`: índice de búsqueda.
- `/rss.xml`: ya pendiente en el ADR.

**Idioma**
- El switch lleva a la ruta equivalente en el otro idioma (si el post no tiene traducción, a la portada de ese idioma) y guarda `localStorage['blog.lang']`.
- No redirigir de forma automática; como mucho, sugerirlo en la primera visita.
- Los textos de la interfaz salen de un dict `STRINGS[lang]` inyectado en Jinja. El diseño trae la lista completa en ES/EN dentro de la lógica de `Blog 1a.dc.html` (objeto `strings`).
- Fechas: «14 NOV» y «14 NOV 2026» con meses `ENE…DIC` / `JAN…DEC`. Reemplazar el filtro `format_date`, hoy fijo en inglés, por uno que reciba `lang`.

**Estado del cliente (vanilla JS o Alpine, mínimo)**
- `blog.textSize`: entero de 15 a 24, 18 por defecto. Se aplica como `--prose-size` en `<html>` **antes del primer pintado**, con un script inline en `<head>`, para evitar el salto.
- Sheet abierto/cerrado: estado local. Esc y tocar el velo lo cierran; foco atrapado dentro mientras está abierto.
- Búsqueda: `q`, resultados, índice activo (teclado en desktop).

**Accesibilidad**
- Áreas táctiles de 44px como mínimo.
- Foco visible en todo con `:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px }` (ya en `broadsheet.css`).
- Sheet y diálogo con `role="dialog"` y `aria-modal`.
- Las planchas `.plate` llevan `aria-hidden`.
- Lista del archivo con `aria-busy` durante el swap.

---

## 9. Orden sugerido de implementación
1. Base: CSS nuevo, `base.html` (header, footer, favicon) y quitar los fantasmas.
2. Portada y `post_list.html`.
3. Artículo: prosa, pygments-light y controles de lectura.
4. Archivo y filtros con HTMX, más los estados.
5. Búsqueda (`/search.json` + mobile + ⌘K).
6. Errores.
7. Idioma: modelo, rutas, strings y fechas.
8. OpenGraph y meta tags.
9. Actualizar el ADR.

## 10. Recursos
- Íconos: Phosphor, solo en peso **duotone**: `magnifying-glass`, `arrow-left`, `arrow-right`, `text-aa`, `link`, `check`, `linkedin-logo`, `x-logo`, `export`, `share-network`, `circle-notch`, `check-circle`, `wifi-slash`, `arrow-clockwise`, `list-bullets`.
- Fuentes: Source Serif 4 (Google Fonts, 400/600/italic 400) y Geist Mono (ya alojada en el repo).
- El anillo: mismos paths que el `favicon.svg` original.
- Las imágenes de post son opcionales y no se usan en la dirección 1a.
