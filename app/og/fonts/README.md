# Fuentes de las imágenes para compartir

Pillow dibuja con archivos TTF u OTF, así que los `woff2` de `static/fonts/` no le sirven. Esta carpeta **no** se sirve como estático: solo la lee `app/og/draw.py`.

| Archivo | Origen | Corte |
| --- | --- | --- |
| `SourceSerif4-14pt-Semibold.ttf` | google/fonts, `ofl/sourceserif4/SourceSerif4[opsz,wght].ttf` (v4.004) | opsz 14, wght 600 |
| `SourceSerif4-14pt-Regular.ttf` | ídem | opsz 14, wght 400 |
| `SourceSerif4-14pt-Italic.ttf` | google/fonts, `ofl/sourceserif4/SourceSerif4-Italic[opsz,wght].ttf` (v4.004) | opsz 14, wght 400 |
| `GeistMono-Regular.ttf` | google/fonts, `ofl/geistmono/GeistMono[wght].ttf` (v1.701) | wght 400 |

- **opsz 14:** el mismo corte óptico que sirve el sitio. La ventana 2 lo fijó así porque es el que sirve Google Fonts y el que muestra el diseño (ver `static/css/fonts.css`). Con el eje automático, los titulares grandes tomarían el corte de display, que es más fino y angosto.
- **Subset:** los mismos 512 caracteres que `static/fonts/SourceSerif4-Variable.woff2` (latin, latin-ext y flechas). Conserva las tablas de kerning y ligaduras (GPOS/GSUB) y no lleva hinting.
- **Licencias:** SIL OFL 1.1, en `SourceSerif4-OFL.txt` y `GeistMono-OFL.txt`.

Para regenerarlas, con [fontTools](https://github.com/fonttools/fonttools) como herramienta suelta (no es dependencia del proyecto):

```bash
uvx --from fonttools fonttools varLib.instancer 'SourceSerif4[opsz,wght].ttf' opsz=14 wght=600 -o ss-600.ttf
uvx --from fonttools fonttools subset ss-600.ttf --unicodes="$U" --layout-features='*' --no-hinting \
    --output-file=SourceSerif4-14pt-Semibold.ttf
```

Para los otros cortes se cambian `wght` y el archivo de origen. `$U` es la lista de códigos del cmap de `static/fonts/SourceSerif4-Variable.woff2`.

Si cambia alguna fuente, subir `RENDER_VERSION` en `app/og/images.py` para que se regeneren todas las imágenes.
