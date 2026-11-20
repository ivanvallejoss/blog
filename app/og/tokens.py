"""
Colores y medidas de las imágenes para compartir (OpenGraph) y del ícono de iOS.

Python no lee variables de CSS: acá quedan como constantes, cada una con el
nombre del token del que sale (`static/css/broadsheet.css`, `blog-tokens.css`)
o de la medida del handoff (README §7 y `design/Blog 1a Extras.dc.html`, E2a,
E2c y el apple-touch-icon). Si cambia un token del sitio, cambia acá.

Las medidas en px son las del prototipo a 1200 × 630, sin escalar. Los
interlineados son los que el prototipo computa: `normal` en el CSS del diseño
hereda el 1.55 del body de Broadsheet.
"""
import math

RGB = tuple[int, int, int]


def hex_rgb(value: str) -> RGB:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def oklch_rgb(lightness: float, chroma: float, hue: float) -> RGB:
    """
    oklch → sRGB de 8 bits: OKLCh → OKLab → LMS → sRGB lineal → gamma sRGB,
    con las matrices de Björn Ottosson (las de CSS Color 4). Un canal fuera
    de rango se recorta, como hace el navegador; los anillos del blog están
    dentro del gamut y no llegan a recortarse.
    """
    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))
    l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_ = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    linear = (
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )

    def encode(channel: float) -> int:
        channel = min(1.0, max(0.0, channel))
        if channel <= 0.0031308:
            channel *= 12.92
        else:
            channel = 1.055 * channel ** (1 / 2.4) - 0.055
        return round(channel * 255)

    return tuple(encode(channel) for channel in linear)


# ── Colores ──────────────────────────────────────────────────────────────
COLOR_BG = hex_rgb("#f3f2f2")             # --color-bg
COLOR_TEXT = hex_rgb("#201e1d")           # --color-text
COLOR_NEUTRAL_700 = hex_rgb("#605d5d")    # --color-neutral-700
COLOR_NEUTRAL_800 = hex_rgb("#444141")    # --color-neutral-800
COLOR_ACCENT_700 = hex_rgb("#006786")     # --color-accent-700
BRAND_RING = oklch_rgb(0.72, 0.15, 68)        # --brand-ring: oklch(0.72 0.15 68), nav y OG
BRAND_RING_SMALL = oklch_rgb(0.68, 0.15, 66)  # --brand-ring-small: oklch(0.68 0.15 66), favicon y touch icon

# ── Anillo ───────────────────────────────────────────────────────────────
# Los tres trazos de static/public/favicon.svg (viewBox 0 0 32 32): arcos de
# radio 12.5 alrededor del centro del viewBox, con punta redonda. El grosor va
# en unidades del viewBox y cambia según el uso.
RING_VIEWBOX = 32
RING_CENTER = (16.0, 16.0)
RING_RADIUS = 12.5
RING_PATHS = (
    "M 16.00 28.50 A 12.5 12.5 0 0 1 3.98 19.45",
    "M 3.62 14.26 A 12.5 12.5 0 0 1 14.26 3.62",
    "M 19.45 3.98 A 12.5 12.5 0 0 1 28.50 16.00",
)

# ── Imagen de post (E2a) ─────────────────────────────────────────────────
OG_WIDTH, OG_HEIGHT = 1200, 630
OG_PAD_Y, OG_PAD_X = 72, 80               # padding: 72px 80px
BODY_LEADING = 1.55                       # line-height del body de broadsheet.css

BRAND_RING_SIZE = 34                      # anillo de 34px
BRAND_RING_STROKE = 3                     # stroke-width 3 (viewBox)
BRAND_GAP = 12                            # gap: 12px entre anillo, «IV» y «/blog»
BRAND_MARK_SIZE = 30                      # «IV» 30px / 600
BRAND_SUB_SIZE = 22                       # «/blog» Geist Mono 22px, neutral-700

TOPIC_SIZE = 22                           # tema 22px, uppercase
TOPIC_TRACKING = 0.1                      # letter-spacing .1em
TITLE_SIZE = 78                           # título 78px / 1.04, peso 600
TITLE_SIZE_LONG = 64                      # con más de ~60 caracteres, 64px
TITLE_LONG_AFTER = 60                     # «si supera ~60 caracteres»
TITLE_SIZE_MIN = 40                       # piso del ajuste de respaldo (ver draw.py)
TITLE_LEADING = 1.04
TITLE_TRACKING = -0.02                    # letter-spacing -.02em
TITLE_MAX_WIDTH = 960                     # max-width 960px, text-wrap: balance
TITLE_MARGIN_TOP = 16                     # margin: 16px 0 36px
TITLE_MARGIN_BOTTOM = 36
TITLE_CLEARANCE = 24                      # aire mínimo bajo la marca (no está en el diseño)
META_SIZE = 22                            # fila mono 22px, uppercase
META_TRACKING = 0.04                      # letter-spacing .04em

# ── Imagen por defecto (E2c) ─────────────────────────────────────────────
DEFAULT_RING_SIZE = 120                   # anillo de 120px
DEFAULT_RING_STROKE = 2.6                 # stroke-width 2.6 (viewBox)
DEFAULT_MARK_SIZE = 110                   # «IV» 110px / 600, line-height 1
DEFAULT_MARK_TRACKING = -0.03             # letter-spacing -.03em (lo hereda «/blog»)
DEFAULT_SUB_SIZE = 56                     # «/blog» Geist Mono 56px
DEFAULT_PHRASE_SIZE = 36                  # frase 36px / 1.3, neutral-800
DEFAULT_PHRASE_LEADING = 1.3
DEFAULT_PHRASE_GAP = 24                   # margin-top 24px
DEFAULT_PHRASE_MAX_WIDTH = 860            # max-width 860px

# ── apple-touch-icon (README §7 · Favicon) ───────────────────────────────
TOUCH_ICON_SIZE = 180                     # 180 × 180, fondo --color-bg
TOUCH_ICON_RING_SIZE = 110                # anillo de 110px, centrado
TOUCH_ICON_RING_STROKE = 2.8              # stroke-width 2.8 (viewBox)
