"""
Formato de fechas del blog. Locale-independent a propósito: el diseño
usa mono en mayúsculas, y depender del locale del server para eso es
una fuente de bugs silenciosos entre dev y producción.
"""
from datetime import datetime

MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)


def format_date(value: datetime) -> str:
    """Ejemplo: 5 Jun 2026 — eyebrow del post y de la fila destacada."""
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}"


def format_date_short(value: datetime) -> str:
    """Ejemplo: 5 Jun — columna derecha de las filas del listado."""
    return f"{value.day} {MONTHS[value.month - 1]}"