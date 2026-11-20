La ventana 1 está cerrada en la rama broadsheet con cinco commits. No hice push ni merge. La portada, una categoría y el post responden 200, /no-existe/ responde 404 con la plantilla nueva, y el log no tiene ningún 404 de archivos estáticos.

1. Qué quedó hecho, por archivo

- docker-compose.yml: la base pasó al puerto 5435, como pediste (el 5433 también estaba ocupado). En tu .env local, que no está versionado, cambié DATABASE_URL al mismo puerto.
- static/css/:
  - Copié los tres CSS del paquete. De broadsheet.css solo saqué el @import de Google Fonts.
  - fonts.css quedó solo con Geist Mono y Source Serif 4.
  - blog.css está reescrito desde cero: reset, contenedor, header, footer y utilidades, mobile primero. El layout cambia a desktop en 768 px y las medidas interpolan entre 390 y 1280.
- static/fonts/: Source Serif 4 alojada en dos archivos, una romana variable 400–600 (164 KB) y una itálica fija en 400 (81 KB), con su licencia OFL. Las dos están recortadas a latin + latin-ext y conservan el ajuste óptico (opsz).
- static/js/htmx.min.js: HTMX 2.0.4.
- static/public/favicon.svg: reescrito según CORRECCIONES.
- Borrados: todo lo que lista CORRECCIONES §1.
- app/i18n.py: STRINGS en ES y EN, más un envoltorio UIText. Sin él, en Jinja t.copy devolvería el método dict.copy en vez del texto. Además, una clave que falta da error en vez de renderizar vacío.
- app/config.py: flag BLOG_LANG_SWITCH, apagado por defecto.
- app/dates.py: los filtros reciben el idioma y devuelven «04 NOV» y «04 NOV 2026».
- app/templating.py: inyecta en todos los templates lang, t, langs, lang_switch_enabled, current_year y rss_url.
- app/selectors.py: get_archive_counts ahora devuelve el número de mes y no el rótulo, porque el rótulo depende del idioma.
- Templates: base.html y partials/brand.html son nuevos. Index, categoría, post, 404 y error quedaron con markup mínimo.
- docs/adrs/broadsheet-en-el-blog.md: el ADR nuevo. El anterior no se tocó.

2. Dónde me aparté del README o de CORRECCIONES

- Fechas con cero: «03 SEP», como hace el prototipo, aunque el README escribe «14 NOV» sin aclarar.
- Footer: sin «·» entre los elementos, separados por 16 px, como el prototipo. El prototipo no tiene footer en desktop: usé el mismo dentro del contenedor de 1120 px.
- RSS: no se muestra mientras no exista la ruta. Aparece solo cuando se registre una ruta llamada rss. Lo preferí a un texto «RSS» que parece link y no lleva a ningún lado.
- Switch ES/EN en mobile: cada botón mide 44×44 para cumplir el mínimo de área táctil. Por eso el switch queda unos 18 px más a la izquierda que en el prototipo. En desktop el área táctil se agranda con un pseudo-elemento invisible y no cambia nada visible.
- Tokens de layout: los agregué en un bloque marcado al final de blog-tokens.css (márgenes, separación entre secciones, paddings del header), para que blog.css no tenga medidas sueltas.
- Flecha ↗: la fuente alojada incluye las flechas, así que «↗» sale en Source Serif. En el prototipo la dibuja una fuente de respaldo y se ve un poco más gruesa.
- Textos que el diseño no trae: sumé footer, «Saltar al contenido», marca, errores y lista vacía. countLine y res(n) quedaron como plantillas con parámetros.

3. Qué afecta a las ventanas siguientes

- uv run fastapi dev app/main.py no arranca, y ya fallaba en main. Como app/ no tiene __init__.py, el import relativo de main.py da error. Verifiqué con uv run uvicorn app.main:app. Agregar un app/__init__.py vacío probablemente lo arregla, pero no lo toqué.
- URLs de tres segmentos o más (por ejemplo /a/b/c/): devuelven {"detail":"Not Found"} en JSON, porque el handler solo atrapa la HTTPException de FastAPI y no la de Starlette. También ya pasaba antes. Le toca a la ventana de errores.
- Textos que siguen fuera del diccionario:
  - Los detail de los routers están escritos en español en el código y la página 404 los muestra.
  - get_tag_counts sigue devolviendo "ALL" desde Python.
- La base local tiene un solo post (presentacion/parte_del_proceso). Para la portada, el archivo y los filtros va a hacer falta más contenido.
- Comentarios que todavía nombran el «rail»: en post.py, render.py y selectors.py.
- La carpeta docs/design_handoff_blog_broadsheet/ sigue sin commitear. No la agregué porque no estaba en el alcance.

4. Qué verifiqué y qué quedó sin verificar

- Rutas: con curl, /, /presentacion/ y el post responden 200; /no-existe/ y /presentacion/nope/ responden 404 con la plantilla nueva. El log no tiene errores ni 404 de estáticos.
- Capturas: saqué capturas headless con Chromium a 390×844, 1280×800, 600 y 800 px, también con el flag del switch encendido en un segundo servidor. Las comparé contra el prototipo abierto desde disco, por imagen y midiendo la posición de cada elemento. El header de desktop coincide con 1–2 px de diferencia. En mobile, la marca y la lupa coinciden, y el switch tiene el corrimiento de 18 px explicado arriba.
- Fechas y textos: probé los filtros de fecha en los dos idiomas y confirmé que todas las claves t.* que usan los templates existen en STRINGS.
- Sin verificar:
  - El footer del prototipo en mobile: está dentro de un contenedor con scroll y no lo pude capturar. Lo comparé por los valores del código.
  - La itálica en uso real.
  - Navegadores que no sean Chromium.
  - El foco con teclado, recorrido a mano.

5. Bloques y clases disponibles

- Bloques de Jinja: title, meta, head, scripts, body_class, header_modifier, header_start, header_center, header_end, content y footer.
- Macros (en partials/brand.html, reciben t): ring(), brand(t, href), back_button(t, href), search_button(t) y lang_switch(t, lang, langs, enabled).
- Clases de layout: .container, .section (separa secciones contiguas), .mt-section, .pt-section, .section-label, .list-reset, .visually-hidden y .skip-link.
- Clases de interacción: .hit (agranda el área táctil a 44 px sin cambiar el tamaño visible), .desktop-only, .mobile-only y .header-icon-btn.
- Modificador del header: .site-header--back, para las páginas con flecha atrás.
- Ganchos para JS: [data-search-open] en el botón de búsqueda y [data-lang] en los botones del switch.
- Metadatos: .meta-mono pasa de 11.5 a 12 px según el ancho.
