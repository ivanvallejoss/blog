# Despliegue de Broadsheet

Lista única de todo lo que hay que hacer a mano para desplegar el rediseño. Junta los pasos de los informes de las ventanas 3, 4, 5 y 6 (`docs/design_handoff_blog_broadsheet/informes/`), sin repeticiones y en orden.

El servidor tiene hoy el blog anterior a Broadsheet: ninguna ventana se desplegó. Esta lista lleva del estado actual al de la rama `opengraph`.

---

## A. En Notion (antes de desplegar)

En la base de posts:

1. **Crear la propiedad `Idioma`**, de tipo **Select**, con dos opciones: `es` y `en`, en minúscula.
   - Se aceptan sin distinguir mayúsculas.
   - Vacía equivale a `es`.
   - Cualquier otro valor cae a español y el sync lo informa.
2. **Crear la propiedad `Resumen`**, de tipo **Text**. Es la bajada escrita a mano: la usan la portada, la búsqueda, el feed y la descripción para compartir. Vacía, se deriva del primer párrafo.
3. **Ponerle `Fecha Publicacion` a todo post en estado `Published`.** Un post publicado sin fecha corta el sync entero. Hoy le falta a «Levantar un servidor sin mirar».
4. **Una traducción es otra página, con su propio `slug`.** Dos posts con el mismo slug hacen fallar el sync, aunque estén en idiomas distintos.
5. **Evitar temas (`categoria`) cuyo slug sea** `en`, `archivo`, `archive`, `search.json`, `rss.xml` o `static`: quedan tapados por una ruta fija. El sync los informa.

## B. En el servidor (en este orden)

1. **Respaldar la base** antes de migrar, con `pg_dump`.
2. **Traer el código** de la rama que se despliegue.
3. **Instalar dependencias:** `uv sync`. La única nueva es Pillow.
4. **Revisar que Pillow tenga kerning:**
   ```bash
   uv run python -c "from PIL import features; print(features.check('raqm'))"
   ```
   Si da `False`, instalar `libfribidi` con el gestor de paquetes del sistema. Sin ella las imágenes se generan igual, pero sin kerning. `og-images` lo avisa.
5. **Variables de entorno** del servicio y de quien corra la CLI:
   - `BLOG_BASE_URL=https://blog.ivanvallejos.dev`. Arma canonical, OpenGraph, `hreflang`, los links de compartir y el feed, y pone el dominio en las imágenes.
   - `BLOG_LANG_SWITCH=1` para mostrar el switch ES/EN. Las rutas `/en/` existen aunque falte.
   - **No** definir `BLOG_ALLOW_SEED`.
   - `BLOG_SQL_ECHO=1` solo si se quiere ver el SQL en el log.
6. **Proxy:** uvicorn o gunicorn con `--proxy-headers` y `--forwarded-allow-ips` para la IP del proxy. Con `BLOG_BASE_URL` definida ya no afecta a las URLs públicas, pero sí a lo que Starlette ve del pedido.
7. **Migrar:** `uv run alembic upgrade head`. Aplica `a7c41e9b2d05` (`lang` y `excerpt`), la única migración del rediseño. Los posts existentes quedan en español.
8. **Carpeta de imágenes:** `static/og/` tiene que existir, o poder crearse, y ser escribible por el usuario que corre el sync y la CLI. El servicio web solo la lee. Si el sync corre por cron, es el usuario del cron.
9. **Sincronizar una vez con `--force`:** `uv run python cli.py sync --force`.
   - Reconvierte todos los posts con el conversor nuevo, el idioma y la bajada de Notion, y el ancla de los títulos en su idioma.
   - Genera las imágenes.
   - Revisar el resumen: tipos de bloque no soportados, `Idioma` desconocidos, temas con slug reservado e imágenes que fallaron.
10. **Generar las imágenes que falten:** `uv run python cli.py og-images`. Escribe las dos por defecto y cualquiera que el sync no haya hecho. Sale con código 1 si alguna falla.
11. **Reiniciar el servicio**, para que tome el código y las variables nuevas.
12. **Purgar la caché de Cloudflare de `/static/`**, o *Purge Everything*. Los estáticos no llevan versión en la URL y cambiaron casi todos:
    - CSS: `fonts.css`, `broadsheet.css`, `blog-tokens.css`, `blog.css` y `pygments-light.css`.
    - JavaScript: `htmx.min.js`, `toast.js`, `loading.js`, `archive.js`, `article.js`, `dialog.js` y `search.js`.
    - Fuentes y `favicon.svg`.

    Las imágenes de `static/og/` no hace falta purgarlas: llevan `?v=` y la versión cambia con la imagen.
13. **Revisar el log:** tienen que llegar las líneas del logger `blog.errors`, con su `[ref …]`. Si gunicorn configura el logging de otra forma, sumar ese logger a su configuración.

## C. Verificar después

1. **Páginas:** `/`, `/en/`, `/archivo/`, `/en/archive/`, un tema y un post en cada idioma responden 200. `/no-existe/` y `/en/no-existe/` responden 404 con la plantilla en su idioma.
2. **Meta tags:** en el código fuente de la portada y de un post, `canonical`, `og:url` y `og:image` empiezan con `https://blog.ivanvallejos.dev/`. Ninguna URL lleva `http://`.
3. **Imágenes:** abrir el `og:image` de un post y el de la portada en los dos idiomas. Las tres tienen que verse, cada una con su fecha y su tema en el idioma correcto.
4. **Tarjetas:** pegar la URL de un post y la de la portada en el [Sharing Debugger de Facebook](https://developers.facebook.com/tools/debug/) y en el [Post Inspector de LinkedIn](https://www.linkedin.com/post-inspector/). Si alguna red tenía una versión vieja en caché, pedirle que vuelva a leer la página.
5. **Feeds:** `/rss.xml` y `/en/rss.xml` pasan el [validador de W3C](https://validator.w3.org/feed/). En un lector, cada entrada muestra el post completo y los links funcionan.
6. **iOS:** `/static/public/apple-touch-icon.png` responde 200. «Agregar a pantalla de inicio» muestra el anillo.
7. **Switch e idioma:** con `BLOG_LANG_SWITCH=1`, el switch lleva a la misma página en el otro idioma. En Search Console, `hreflang` no informa errores (puede tardar días).
8. **Búsqueda:** ⌘K en desktop y la lupa en mobile encuentran posts en el idioma de la página.
9. **Próximo sync:** al editar un post en Notion y correr `sync`, la línea «Imágenes: …» muestra 1 generada, y el `?v=` de su `og:image` cambia.
