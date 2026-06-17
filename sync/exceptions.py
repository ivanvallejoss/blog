# sync/exceptions.py
class CategoriaFaltanteError(Exception):
    """
    Error que detecta la faltante de `categoria` en un post proveniente de Notion.
    """
    pass