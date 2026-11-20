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
