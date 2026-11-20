"""
Pruebas de la lectura de propiedades de Notion (`notion/client.py`) y de lo
que el sync hace con ellas (`sync/services.py`). Las páginas de Notion están
escritas a mano, con la forma de la API; la sesión de la base es un doble.

    uv run python -m unittest
"""
import unittest
from unittest import mock

from app.models.post import Post
from notion.client import get_details_from_post, read_lang
from sync.services import reserved_topics, sync_posts


def page(notion_id="p1", lang=..., excerpt=..., category="concurrencia"):
    """
    Página de la base de Notion. `lang` y `excerpt`: `...` deja la propiedad
    afuera (la base todavía no la tiene); None la deja vacía.
    """
    properties = {
        "Titulo": {"type": "title", "title": [{"plain_text": "Un post"}]},
        "slug": {"type": "rich_text", "rich_text": [{"plain_text": "un-post"}]},
        "Fecha Publicacion": {"type": "date", "date": {"start": "2026-11-14"}},
        "categoria": {"type": "select", "select": {"name": category} if category else None},
    }
    if lang is not ...:
        properties["Idioma"] = {"type": "select", "select": {"name": lang} if lang is not None else None}
    if excerpt is not ...:
        rich = [{"plain_text": part} for part in excerpt] if excerpt is not None else []
        properties["Resumen"] = {"type": "rich_text", "rich_text": rich}
    return {"id": notion_id, "last_edited_time": "2026-11-15T10:00:00.000Z", "properties": properties}


class ReadProperties(unittest.TestCase):
    def test_missing_properties(self):
        details = get_details_from_post(page())
        self.assertEqual(details["lang"], "es")
        self.assertIsNone(details["lang_unknown"])
        self.assertIsNone(details["excerpt"])

    def test_empty_properties(self):
        details = get_details_from_post(page(lang=None, excerpt=None))
        self.assertEqual(details["lang"], "es")
        self.assertIsNone(details["lang_unknown"])
        self.assertIsNone(details["excerpt"])

    def test_blank_excerpt_is_none(self):
        self.assertIsNone(get_details_from_post(page(excerpt=["   "]))["excerpt"])

    def test_values(self):
        details = get_details_from_post(page(lang="en", excerpt=["Una bajada ", "escrita a mano."]))
        self.assertEqual(details["lang"], "en")
        self.assertIsNone(details["lang_unknown"])
        self.assertEqual(details["excerpt"], "Una bajada escrita a mano.")

    def test_lang_is_case_insensitive(self):
        self.assertEqual(read_lang(page(lang=" EN ")["properties"]), ("en", None))

    def test_unknown_lang_falls_back_to_spanish(self):
        details = get_details_from_post(page(lang="pt"))
        self.assertEqual(details["lang"], "es")
        self.assertEqual(details["lang_unknown"], "pt")

    def test_wrong_property_type_is_ignored(self):
        props = page()["properties"]
        props["Idioma"] = {"type": "rich_text", "rich_text": [{"plain_text": "en"}]}
        self.assertEqual(read_lang(props), ("es", None))


class Sync(unittest.TestCase):
    def setUp(self):
        # Los avisos del sync se prueban por el reporte; no ensucian la salida.
        logger = mock.patch("sync.services.logger")
        self.logger = logger.start()
        self.addCleanup(logger.stop)
        # Las imágenes para compartir tienen sus propias pruebas (test_og.py).
        images = mock.patch("sync.services.refresh_images")
        self.refresh_images = images.start()
        self.addCleanup(images.stop)

    def run_sync(self, *pages):
        db = mock.MagicMock()
        db.query.return_value.all.return_value = []
        with mock.patch("sync.services.get_posts", return_value=list(pages)), \
             mock.patch("sync.services.get_page_blocks", return_value=[
                 {"type": "heading_2", "heading_2": {"rich_text": [{"plain_text": "Hola", "annotations": {}}]}},
             ]):
            report = sync_posts(db)
        posts = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], Post)]
        return report, posts

    def test_without_the_new_properties(self):
        report, [post] = self.run_sync(page())
        self.assertEqual(report.created, 1)
        self.assertEqual(post.lang, "es")
        self.assertIsNone(post.excerpt)
        self.assertEqual(report.unknown_lang, [])

    def test_english_post_with_excerpt(self):
        report, [post] = self.run_sync(page(lang="en", excerpt=["A hand-written excerpt."]))
        self.assertEqual(post.lang, "en")
        self.assertEqual(post.excerpt, "A hand-written excerpt.")
        # El ancla de los títulos, en el idioma del post.
        self.assertIn('title="Link to this section"', post.content_html)

    def test_unknown_lang_is_reported(self):
        report, [post] = self.run_sync(page(lang="Portugués"))
        self.assertEqual(post.lang, "es")
        self.assertIn('title="Enlace a esta sección"', post.content_html)
        self.assertEqual(report.unknown_lang, [("Un post", "p1", "Portugués")])

    def test_reserved_topic_is_reported(self):
        report, _ = self.run_sync(page(category="Archivo"))
        self.assertEqual(report.reserved_topics, [("Archivo", "archivo")])


class ReservedTopics(unittest.TestCase):
    def test_collisions(self):
        names = ["concurrencia", "EN", "archive", "Archivo", "search.json", "static", "life"]
        self.assertEqual(
            reserved_topics(names),
            [("Archivo", "archivo"), ("EN", "en"), ("archive", "archive"), ("static", "static")],
        )


if __name__ == "__main__":
    unittest.main()
