from datetime import datetime
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

def _format_date(value: datetime) -> str:
    """
    Filtro Jinja2 para fechas. Locale-independent.
    Ejemplo: 5 jun 2025
    """
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    return f"{value.day} {months[value.month - 1]} {value.year}"

templates.env.filters["format_date"] = _format_date

