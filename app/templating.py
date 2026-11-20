from fastapi.templating import Jinja2Templates

from .dates import format_date, format_date_short

templates = Jinja2Templates(directory="app/templates")

templates.env.filters["format_date"] = format_date
templates.env.filters["format_date_short"] = format_date_short