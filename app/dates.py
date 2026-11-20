"""
Formato de fechas del blog. Independiente del locale a propósito: el diseño
usa mono en mayúsculas, y depender del locale del server para eso es
una fuente de bugs silenciosos entre dev y producción.

Día con dos dígitos, como en el diseño («03 SEP»): las fechas se alinean en
columna en el archivo.
"""
from datetime import datetime

MONTHS = {
    "es": ("ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
           "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"),
    "en": ("JAN", "FEB", "MAR", "APR", "MAY", "JUN",
           "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"),
}


def month_label(month: int, lang: str) -> str:
    """Ejemplo: 11, "es" → NOV."""
    return MONTHS[lang][month - 1]


def format_date_short(value: datetime, lang: str) -> str:
    """Ejemplo: 14 NOV — filas de la portada y del archivo."""
    return f"{value.day:02d} {month_label(value.month, lang)}"


def format_date(value: datetime, lang: str) -> str:
    """Ejemplo: 14 NOV 2026 — cabecera del post."""
    return f"{format_date_short(value, lang)} {value.year}"
