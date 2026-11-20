# sync/exceptions.py
class EsquemaNotionError(Exception):
    """
    A la base de Notion le falta una propiedad obligatoria (o tiene otro tipo):
    el sync no arranca, porque saltearía todos los posts. `problems` dice qué
    corregir en Notion.
    """

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems
