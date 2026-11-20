# Arreglo · El sync no se corta por un post mal cargado

Está en la rama `opengraph`, en 7 commits contando este informe, sin push ni merge. Pasan 173 pruebas, 13 de ellas nuevas. Un post bien cargado se sincroniza igual que antes.

## Qué cambió, por archivo

- **`notion/client.py`:**
  - `REQUIRED_PROPERTIES` (`Titulo`, `slug`, `Fecha Publicacion`, `categoria`, con su tipo) y un solo lector, `read_required()`. Devuelve los valores y la lista de lo que falta, en palabras que dicen qué corregir: vacío, solo espacios, o una fecha que `fromisoformat` no lee.
  - `get_details_from_post` ya no falla: agrega `problems` y `created_time`.
  - `schema_problems()` detecta las propiedades obligatorias que la base no tiene en ninguna página, o que tienen otro tipo.
- **`sync/exceptions.py`:** sale `CategoriaFaltanteError` y entra `EsquemaNotionError(problems)`.
- **`sync/services.py`:**
  - Antes de leer o escribir la base, `schema_problems` decide si el sync arranca. Si falta una propiedad, se levanta `EsquemaNotionError` y no se toca nada.
  - Después, todos los posts pasan por el mismo camino. Los que tienen `problems` o repiten slug se saltean, quedan en `SyncReport.rejected` y en `sync_errors`, y van al log.
  - Como con el post sin tema de antes, no entran en `seen_ids`: si ya estaban en la base, se borran hasta que se corrijan.
  - **Slug repetido** (`_drop_duplicate_slugs`): se conserva el que ya estaba publicado con ese slug. Si ninguno lo estaba, el que se creó antes en Notion, y a igual fecha el de menor id.
- **`cli.py`:**
  - La línea del resumen suma «N salteados» y lista cada post con su título (o «Post sin título») y su id de Notion, con los motivos.
  - Con una propiedad ausente imprime «El sync no se hizo…», qué propiedad falta, y sale con código 1.
- **`app/i18n.py`:** `presentacion` → «introduction».
- **Pruebas:**
  - `tests/test_notion.py`: la fábrica `page()` acepta título, slug, fecha, creación y `drop`.
  - 13 casos nuevos: cada dato obligatorio vacío, título con solo espacios, fecha ilegible, varios a la vez, post malo entre dos buenos, post publicado que se rompe, propiedad ausente (sin escribir nada), tipo equivocado, los dos criterios de slug repetido y la salida de la CLI.
  - `tests/test_og.py`: un doble ajustado.
- **Docs:**
  - `README.md`: cuáles propiedades son obligatorias y qué pasa si faltan.
  - `docs/despliegue-broadsheet.md`: el bloqueo por fecha pasa a ser «se saltea y se lista». También explica cómo leer el resumen.

## Salida real del sync

**Contra el Notion real**, `sync --force`. Ya no hay un post sin fecha: «Levantar un servidor sin mirar» tiene fecha (20 nov) y es el único publicado, porque «Parte del Proceso» ya no lo está. Terminó sin salteados:

```
Sync: 1 nuevos, 0 reconvertidos, 0 sin cambios, 13 borrados, 0 salteados.
Imágenes: 1 generadas, 0 sin cambios, 13 borradas, 0 por defecto escritas.
```

**El caso del brief.** Para reproducirlo sin escribir en Notion, corrí la CLI real con las páginas reales más dos copias en memoria: una sin fecha y otra con el mismo slug y creada después. Todo contra la base local:

```
Sync: 0 nuevos, 0 reconvertidos, 1 sin cambios, 0 borrados, 2 salteados.
Salteados (no se publicaron; si ya estaban en el sitio, se quitaron hasta que se corrijan en Notion):
  «Levantar un servidor sin mirar» (00000000-0000-4000-8000-00000000da7e): le falta la fecha de publicación (propiedad «Fecha Publicacion»).
  «Copia con el mismo slug» (00000000-0000-4000-8000-0000000d0b1e): tiene el mismo slug «levantar_un_servidor_sin_mirar» que «Levantar un servidor sin mirar» (41e27bfa-15f5-80fa-9198-e0daf1282d2b), que se conservó porque ya estaba publicado con ese slug; cambiá el slug de uno de los dos.
Imágenes: 0 generadas, 1 sin cambios, 0 borradas, 0 por defecto escritas.
```

**Propiedad ausente**, con las páginas reales sin `Fecha Publicacion` (código de salida 1):

```
El sync no se hizo: a la base de Notion le falta algo obligatorio. No se cambió nada.
  La base de Notion no tiene la propiedad «Fecha Publicacion» (tipo Fecha). Creala con ese nombre exacto.
```

Después volví a correr `sync` (1 sin cambios) y `BLOG_ALLOW_SEED=1 seed-dev` (12 posts, 12 imágenes).

## Otros puntos frágiles que vi (sin arreglar)

1. **Título o slug de más de 100 caracteres.** Las columnas son `String(100)`, y Postgres rechaza el `INSERT`: el sync entero hace rollback.
2. **Slug que pasa de un post a otro en el mismo sync.** Por ejemplo, se borra el post A en Notion y se crea B con su slug, o dos posts intercambian slugs. SQLAlchemy escribe el alta o el cambio antes del `DELETE` del final, y salta la restricción de unicidad: se corta todo.
3. **Dos temas cuyo nombre da el mismo slug** («Diseño» y «diseno», o «Design System» y «design system»). `Category.slug` es único, así que el segundo hace fallar el sync.
4. **Slug con caracteres que no sirven en una URL** (espacios, `/`, `?`). No corta el sync, pero el post queda inaccesible o tapa otra ruta. No se valida ni se normaliza.
5. **Fecha con hora y zona horaria.** Se guarda la hora local de Notion sin convertir, mientras que el feed y `article:published_time` la tratan como UTC. No corta nada, pero puede correr la fecha un día.
6. **Los avisos de salteados salen dos veces en la terminal:** una por `logging.warning` y otra en el resumen. Es el mismo criterio que ya seguían los tipos no soportados y los idiomas desconocidos.

## Sin verificar

- Con el Notion real, el post sin fecha y el slug repetido: el caso ya no existe allá. Lo probé con copias en memoria de las páginas reales, por la CLI real y contra la base local.
- Una fecha con un formato que Notion realmente devuelva y `fromisoformat` no lea. La API siempre manda ISO 8601; el caso está cubierto con un valor inventado.
- La propiedad con el tipo equivocado en la base real (está cubierta por prueba).
