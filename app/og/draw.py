"""
Dibujo de las imágenes para compartir y del ícono de iOS, con Pillow.

Reproduce el prototipo (`design/Blog 1a Extras.dc.html`, E2a, E2c y el
apple-touch-icon) con el mismo modelo de caja de línea que usa Chromium, así
las posiciones coinciden con el HTML del diseño:

- **Línea:** el alto es el line-height. El área de contenido es el ascendente
  más el descendente de la fuente (tabla hhea), cada uno redondeado al píxel.
  La mitad de lo que sobra (half-leading), redondeada hacia abajo, va arriba.
  La línea de base queda en `top + floor(half_leading) + ascendente`.
- **letter-spacing:** se suma después de cada carácter, también del último,
  como en CSS. Con tracking distinto de cero se apagan las ligaduras, como
  hace el navegador.
- **Kerning:** el de la fuente (GPOS), mediante libraqm. Sin raqm, Pillow cae
  al motor básico, que no kernea (ver `RAQM`).
- **text-wrap: balance:** Pillow no lo trae. `balance()` hace lo mismo que
  Chromium: busca el ancho más angosto que mantiene la cantidad de líneas
  del partido normal.

El anillo se dibuja como polígono sobre una máscara ocho veces más grande y se
reduce promediando: los bordes y las puntas redondas quedan suaves. El texto
lo suaviza FreeType.
"""
import math
import re
import struct
import unicodedata
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, features

from . import tokens as tk

FONT_DIR = Path(__file__).parent / "fonts"
FONT_FILES = {
    "serif": "SourceSerif4-14pt-Regular.ttf",
    "serif-semibold": "SourceSerif4-14pt-Semibold.ttf",
    "serif-italic": "SourceSerif4-14pt-Italic.ttf",
    "mono": "GeistMono-Regular.ttf",
}

# libraqm da el kerning de la fuente y permite apagar ligaduras. Las ruedas de
# Pillow lo traen, pero necesita libfribidi en el sistema: sin ella, el texto
# sale igual, sin kerning (`cli.py og-images` lo avisa).
RAQM = features.check("raqm")
_LAYOUT = ImageFont.Layout.RAQM if RAQM else ImageFont.Layout.BASIC
_NO_LIGATURES = ["-liga", "-clig"]

SUPERSAMPLE = 8      # escala de la máscara del anillo
_ARC_STEP = 0.5      # grados entre puntos del polígono del arco


# ── Fuentes y estilos ────────────────────────────────────────────────────

@lru_cache(maxsize=None)
def _vertical_metrics(face: str) -> tuple[float, float]:
    """(ascendente, descendente) de la tabla hhea, en em."""
    data = (FONT_DIR / FONT_FILES[face]).read_bytes()
    tables = {}
    (count,) = struct.unpack(">H", data[4:6])
    for i in range(count):
        tag, _, offset, _ = struct.unpack(">4sIII", data[12 + 16 * i: 28 + 16 * i])
        tables[tag] = offset
    (units_per_em,) = struct.unpack(">H", data[tables[b"head"] + 18: tables[b"head"] + 20])
    ascender, descender = struct.unpack(">hh", data[tables[b"hhea"] + 4: tables[b"hhea"] + 8])
    return ascender / units_per_em, -descender / units_per_em


@lru_cache(maxsize=64)
def _font(face: str, size: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / FONT_FILES[face]), size, layout_engine=_LAYOUT)


@dataclass(frozen=True)
class Style:
    face: str
    size: float
    color: tuple[int, int, int]
    tracking: float = 0.0    # letter-spacing en px
    leading: float = tk.BODY_LEADING

    @property
    def font(self) -> ImageFont.FreeTypeFont:
        return _font(self.face, self.size)

    @property
    def line_height(self) -> float:
        return self.size * self.leading

    @property
    def features(self):
        if not RAQM:
            return None
        return _NO_LIGATURES if self.tracking else None

    def baseline(self, line_top: float, line_height: float | None = None) -> float:
        """Línea de base de una línea de este estilo que empieza en `line_top`."""
        ascent, descent = _vertical_metrics(self.face)
        ascent, descent = round(ascent * self.size), round(descent * self.size)
        line_height = self.line_height if line_height is None else line_height
        return line_top + math.floor((line_height - ascent - descent) / 2) + ascent


def advance(text: str, style: Style) -> float:
    """Ancho de `text` como lo mide CSS: avances, kerning y tracking por carácter."""
    if not text:
        return 0.0
    return style.font.getlength(text, features=style.features) + style.tracking * len(text)


def draw_text(draw: ImageDraw.ImageDraw, x: float, baseline: float, text: str, style: Style) -> float:
    """Dibuja `text` con su línea de base en `baseline`; devuelve el ancho."""
    font, feats = style.font, style.features
    if not style.tracking:
        draw.text((x, baseline), text, font=font, fill=style.color, anchor="ls", features=feats)
        return advance(text, style)
    # Con tracking, carácter por carácter. La posición de cada uno sale de
    # medir el texto hasta él inclusive y restar su propio avance: así entra
    # el kerning con el anterior.
    for i, char in enumerate(text):
        if char.isspace():
            continue
        pen = font.getlength(text[:i + 1], features=feats) - font.getlength(char, features=feats)
        draw.text((x + pen + style.tracking * i, baseline), char, font=font,
                  fill=style.color, anchor="ls", features=feats)
    return advance(text, style)


# ── Partido de líneas ────────────────────────────────────────────────────
#
# Una palabra es una lista de tramos (texto, estilo): «concurrencia,» en la
# frase por defecto es un tramo en itálica y otro en romana. Las palabras se
# separan con un espacio del estilo base.

Word = list[tuple[str, Style]]


def _word_width(word: Word) -> float:
    return sum(advance(text, style) for text, style in word)


def _line_width(line: list[Word], space: float) -> float:
    return sum(_word_width(word) for word in line) + space * max(0, len(line) - 1)


def _split_long_word(word: Word, max_width: float) -> list[Word]:
    """Una palabra más ancha que la columna se corta por caracteres (respaldo)."""
    pieces, current = [], []
    for text, style in word:
        for char in text:
            candidate = current + [(char, style)]
            if current and _word_width(candidate) > max_width:
                pieces.append(current)
                candidate = [(char, style)]
            current = candidate
    if current:
        pieces.append(current)
    return pieces


def wrap(words: list[Word], max_width: float, space: float) -> list[list[Word]]:
    """Partido normal (greedy), como `text-wrap: wrap`."""
    lines: list[list[Word]] = []
    current: list[Word] = []
    for word in words:
        for piece in (_split_long_word(word, max_width) if _word_width(word) > max_width else [word]):
            if current and _line_width(current + [piece], space) > max_width + 0.01:
                lines.append(current)
                current = []
            current.append(piece)
    if current:
        lines.append(current)
    return lines


def balance(words: list[Word], max_width: float, space: float) -> list[list[Word]]:
    """
    `text-wrap: balance`: el mismo número de líneas que el partido normal,
    con el ancho más angosto que lo permite (búsqueda binaria, como Chromium).
    Las líneas quedan parejas y ninguna pasa de `max_width`.
    """
    lines = wrap(words, max_width, space)
    if len(lines) < 2:
        return lines
    low = max(min(_word_width(word), max_width) for word in words) - 0.01
    high = max_width
    while high - low > 0.25:
        middle = (low + high) / 2
        if len(wrap(words, middle, space)) <= len(lines):
            high = middle
        else:
            low = middle
    return wrap(words, high, space)


def _plain_words(text: str, style: Style) -> list[Word]:
    return [[(word, style)] for word in text.split()]


_EMPHASIS = re.compile(r"\*([^*]+)\*")


def rich_words(text: str, base: Style, emphasis: Style) -> list[Word]:
    """
    Palabras de un texto con `*énfasis*` (la frase por defecto, desde
    app/i18n.py): lo que va entre asteriscos sale en `emphasis`.
    """
    runs, position = [], 0
    for match in _EMPHASIS.finditer(text):
        runs.append((text[position:match.start()], base))
        runs.append((match.group(1), emphasis))
        position = match.end()
    runs.append((text[position:], base))

    words: list[Word] = [[]]
    for chunk, style in runs:
        for i, part in enumerate(re.split(r"\s+", chunk)):
            if i > 0 and words[-1]:
                words.append([])
            if part:
                words[-1].append((part, style))
    return [word for word in words if word]


def _draw_line(draw, x: float, baseline: float, line: list[Word], space: float) -> None:
    for i, word in enumerate(line):
        if i:
            x += space
        for text, style in word:
            x += draw_text(draw, x, baseline, text, style)


# ── Anillo ───────────────────────────────────────────────────────────────

_ARC = re.compile(r"M\s*([\d.]+)\s+([\d.]+)\s+A\s*([\d.]+)\s+[\d.]+\s+0\s+0\s+1\s+([\d.]+)\s+([\d.]+)")


@lru_cache(maxsize=None)
def ring_arcs() -> tuple[tuple[float, float], ...]:
    """
    (ángulo inicial, ángulo final) en grados de cada trazo de RING_PATHS,
    medidos desde el centro del viewBox con y hacia abajo, como SVG. El flag
    de barrido 1 de los tres path recorre los ángulos en sentido creciente.
    """
    cx, cy = tk.RING_CENTER
    arcs = []
    for path in tk.RING_PATHS:
        x1, y1, radius, x2, y2 = map(float, _ARC.match(path).groups())
        assert abs(radius - tk.RING_RADIUS) < 1e-9, path
        for x, y in ((x1, y1), (x2, y2)):
            assert abs(math.hypot(x - cx, y - cy) - radius) < 0.02, path
        start = math.degrees(math.atan2(y1 - cy, x1 - cx)) % 360
        end = math.degrees(math.atan2(y2 - cy, x2 - cx)) % 360
        if end <= start:
            end += 360
        arcs.append((start, end))
    return tuple(arcs)


def draw_ring(image: Image.Image, x: float, y: float, size: float, stroke: float, color) -> None:
    """
    Anillo de `size` px con su esquina superior izquierda en (x, y), con el
    trazo en unidades del viewBox (`stroke-width`), como el SVG de la marca.
    """
    ss = SUPERSAMPLE
    scale = size / tk.RING_VIEWBOX * ss
    left, top = math.floor(x), math.floor(y)
    offset_x, offset_y = (x - left) * ss, (y - top) * ss
    box = math.ceil(size) + 2
    mask = Image.new("L", (box * ss, box * ss), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = tk.RING_CENTER
    radius, half = tk.RING_RADIUS * scale, stroke / 2 * scale

    def point(angle: float, r: float) -> tuple[float, float]:
        rad = math.radians(angle)
        return (offset_x + cx * scale + r * math.cos(rad), offset_y + cy * scale + r * math.sin(rad))

    for start, end in ring_arcs():
        steps = max(2, math.ceil((end - start) / _ARC_STEP))
        angles = [start + (end - start) * i / steps for i in range(steps + 1)]
        outline = [point(a, radius + half) for a in angles] + [point(a, radius - half) for a in reversed(angles)]
        draw.polygon(outline, fill=255)
        for angle in (start, end):          # stroke-linecap: round
            px, py = point(angle, radius)
            draw.ellipse((px - half, py - half, px + half, py + half), fill=255)

    mask = mask.reduce(ss)
    image.paste(color, (left, top, left + box, top + box), mask)


# ── Composiciones ────────────────────────────────────────────────────────

def _brand(image: Image.Image, draw: ImageDraw.ImageDraw, x: float, top: float, mark: str, sub: str) -> None:
    """Marca de E2a: anillo, «IV» y «/blog» centrados en una fila (flex, gap 12)."""
    mark_style = Style("serif-semibold", tk.BRAND_MARK_SIZE, tk.COLOR_TEXT)
    sub_style = Style("mono", tk.BRAND_SUB_SIZE, tk.COLOR_NEUTRAL_700)
    row = max(tk.BRAND_RING_SIZE, mark_style.line_height, sub_style.line_height)

    draw_ring(image, x, top + (row - tk.BRAND_RING_SIZE) / 2, tk.BRAND_RING_SIZE,
              tk.BRAND_RING_STROKE, tk.BRAND_RING)
    x += tk.BRAND_RING_SIZE + tk.BRAND_GAP
    x += draw_text(draw, x, mark_style.baseline(top + (row - mark_style.line_height) / 2), mark, mark_style)
    x += tk.BRAND_GAP
    draw_text(draw, x, sub_style.baseline(top + (row - sub_style.line_height) / 2), sub, sub_style)


def brand_row_height() -> float:
    return max(tk.BRAND_RING_SIZE, tk.BRAND_MARK_SIZE * tk.BODY_LEADING, tk.BRAND_SUB_SIZE * tk.BODY_LEADING)


@dataclass
class TitleLayout:
    size: float
    lines: list[str]
    top: float              # borde superior del bloque del título
    topic_top: float        # borde superior de la línea del tema


def layout_title(title: str) -> TitleLayout:
    """
    Tamaño y partido del título en la imagen de post.

    78 px, o 64 px si pasa de TITLE_LONG_AFTER caracteres (handoff). El
    partido es equilibrado dentro de 960 px. El bloque se apoya sobre la fila
    de autor, y el tema va encima. Si con eso el tema quedara a menos de
    TITLE_CLEARANCE de la marca, el título baja de a 2 px hasta entrar. Con
    los 100 caracteres que admite la columna no hace falta (lo cubre una
    prueba), pero un título de palabras muy anchas tampoco se sale.
    """
    title = unicodedata.normalize("NFC", " ".join(title.split()))
    meta_top = tk.OG_HEIGHT - tk.OG_PAD_Y - tk.META_SIZE * tk.BODY_LEADING
    title_bottom = meta_top - tk.TITLE_MARGIN_BOTTOM
    ceiling = tk.OG_PAD_Y + brand_row_height() + tk.TITLE_CLEARANCE
    topic_height = tk.TOPIC_SIZE * tk.BODY_LEADING

    size = tk.TITLE_SIZE if len(title) <= tk.TITLE_LONG_AFTER else tk.TITLE_SIZE_LONG
    while True:
        style = title_style(size)
        lines = balance(_plain_words(title, style), tk.TITLE_MAX_WIDTH, advance(" ", style))
        top = title_bottom - len(lines) * style.line_height
        topic_top = top - tk.TITLE_MARGIN_TOP - topic_height
        if topic_top >= ceiling or size <= tk.TITLE_SIZE_MIN:
            text_lines = [" ".join("".join(t for t, _ in word) for word in line) for line in lines]
            return TitleLayout(size, text_lines, top, topic_top)
        size -= 2


def title_style(size: float) -> Style:
    return Style("serif-semibold", size, tk.COLOR_TEXT, tracking=tk.TITLE_TRACKING * size,
                 leading=tk.TITLE_LEADING)


def post_card(*, title: str, topic: str, meta: str, domain: str, mark: str, sub: str) -> Image.Image:
    """
    Imagen de post (E2a), 1200 × 630: marca arriba a la izquierda; abajo el
    tema, el título y la fila con autor · fecha · minutos y el dominio.
    `meta` ya viene armado en el idioma del post; se pasa a mayúsculas como el
    `text-transform` del diseño (el dominio no).
    """
    image = Image.new("RGB", (tk.OG_WIDTH, tk.OG_HEIGHT), tk.COLOR_BG)
    draw = ImageDraw.Draw(image)
    _brand(image, draw, tk.OG_PAD_X, tk.OG_PAD_Y, mark, sub)

    meta_style = Style("mono", tk.META_SIZE, tk.COLOR_NEUTRAL_700, tracking=tk.META_TRACKING * tk.META_SIZE)
    meta_top = tk.OG_HEIGHT - tk.OG_PAD_Y - meta_style.line_height
    meta_baseline = meta_style.baseline(meta_top)
    draw_text(draw, tk.OG_PAD_X, meta_baseline, meta.upper(), meta_style)
    if domain:
        right = tk.OG_WIDTH - tk.OG_PAD_X
        draw_text(draw, right - advance(domain, meta_style), meta_baseline, domain, meta_style)

    layout = layout_title(title)
    style = title_style(layout.size)
    for i, line in enumerate(layout.lines):
        line_top = layout.top + i * style.line_height
        draw_text(draw, tk.OG_PAD_X, style.baseline(line_top), line, style)

    topic_style = Style("serif", tk.TOPIC_SIZE, tk.COLOR_ACCENT_700, tracking=tk.TOPIC_TRACKING * tk.TOPIC_SIZE)
    draw_text(draw, tk.OG_PAD_X, topic_style.baseline(layout.topic_top), topic.upper(), topic_style)
    return image


def default_card(*, phrase: str, mark: str, sub: str) -> Image.Image:
    """
    Imagen por defecto (E2c), 1200 × 630: anillo grande arriba a la izquierda;
    abajo «IV/blog» y la frase, con su palabra en itálica (`*así*`).
    """
    image = Image.new("RGB", (tk.OG_WIDTH, tk.OG_HEIGHT), tk.COLOR_BG)
    draw = ImageDraw.Draw(image)
    draw_ring(image, tk.OG_PAD_X, tk.OG_PAD_Y, tk.DEFAULT_RING_SIZE, tk.DEFAULT_RING_STROKE, tk.BRAND_RING)

    roman = Style("serif", tk.DEFAULT_PHRASE_SIZE, tk.COLOR_NEUTRAL_800, leading=tk.DEFAULT_PHRASE_LEADING)
    italic = replace(roman, face="serif-italic")
    words = rich_words(unicodedata.normalize("NFC", phrase), roman, italic)
    space = advance(" ", roman)
    lines = wrap(words, tk.DEFAULT_PHRASE_MAX_WIDTH, space)
    phrase_top = tk.OG_HEIGHT - tk.OG_PAD_Y - len(lines) * roman.line_height
    for i, line in enumerate(lines):
        _draw_line(draw, tk.OG_PAD_X, roman.baseline(phrase_top + i * roman.line_height), line, space)

    # «IV» y «/blog» comparten línea (line-height 1) y línea de base. El
    # letter-spacing de -.03em se calcula sobre los 110 px y «/blog» lo hereda
    # en px, como en CSS.
    tracking = tk.DEFAULT_MARK_TRACKING * tk.DEFAULT_MARK_SIZE
    mark_style = Style("serif-semibold", tk.DEFAULT_MARK_SIZE, tk.COLOR_TEXT, tracking=tracking, leading=1)
    sub_style = Style("mono", tk.DEFAULT_SUB_SIZE, tk.COLOR_NEUTRAL_700, tracking=tracking, leading=1)
    mark_top = phrase_top - tk.DEFAULT_PHRASE_GAP - mark_style.line_height
    baseline = mark_style.baseline(mark_top)
    x = tk.OG_PAD_X + draw_text(draw, tk.OG_PAD_X, baseline, mark, mark_style)
    draw_text(draw, x, baseline, sub, sub_style)
    return image


def touch_icon() -> Image.Image:
    """apple-touch-icon de 180 × 180: fondo de papel y el anillo de 110 px centrado."""
    size = tk.TOUCH_ICON_SIZE
    image = Image.new("RGB", (size, size), tk.COLOR_BG)
    offset = (size - tk.TOUCH_ICON_RING_SIZE) / 2
    draw_ring(image, offset, offset, tk.TOUCH_ICON_RING_SIZE, tk.TOUCH_ICON_RING_STROKE, tk.BRAND_RING_SMALL)
    return image
