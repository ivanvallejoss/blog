"""
Pruebas de la lectura de propiedades de Notion (`notion/client.py`) y de lo
que el sync hace con ellas (`sync/services.py`). Las páginas de Notion están
escritas a mano, con la forma de la API; la sesión de la base es un doble.

    uv run python -m unittest
"""
import unittest
from datetime import datetime
from unittest import mock

from app.models.post import Post
from typer.testing import CliRunner

import cli
from notion.client import get_details_from_post, read_lang, schema_problems
from sync.exceptions import EsquemaNotionError
from sync.services import SyncReport, reserved_topics, sync_posts


def page(notion_id="p1", lang=..., excerpt=..., category="concurrencia", title="Un post",
         slug="un-post", date="2026-11-14", created="2026-11-01T10:00:00.000Z", drop=()):
    """
    Página de la base de Notion. `lang` y `excerpt`: `...` deja la propiedad
    afuera (la base todavía no la tiene); None la deja vacía. `title`,
    `slug`, `date` y `category` vacíos o None dejan vacía la propiedad
    obligatoria; `drop` saca propiedades (la base no las tiene).
    """
    properties = {
        "Titulo": {"type": "title", "title": [{"plain_text": title}] if title else []},
        "slug": {"type": "rich_text", "rich_text": [{"plain_text": slug}] if slug else []},
        "Fecha Publicacion": {"type": "date", "date": {"start": date} if date else None},
        "categoria": {"type": "select", "select": {"name": category} if category else None},
    }
    for name in drop:
        properties.pop(name)
    if lang is not ...:
        properties["Idioma"] = {"type": "select", "select": {"name": lang} if lang is not None else None}
    if excerpt is not ...:
        rich = [{"plain_text": part} for part in excerpt] if excerpt is not None else []
        properties["Resumen"] = {"type": "rich_text", "rich_text": rich}
    return {"id": notion_id, "created_time": created, "last_edited_time": "2026-11-15T10:00:00.000Z",
            "properties": properties}


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

    def run_sync(self, *pages, existing=()):
        db = mock.MagicMock()

        def query(model):
            q = mock.MagicMock()
            q.all.return_value = list(existing) if model is Post else []
            return q
        db.query.side_effect = query
        self.db = db
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


    # — posts mal cargados (arreglo del sync) —

    def test_each_missing_required_value_skips_the_post(self):
        cases = {
            "título": dict(title=""),
            "slug": dict(slug=""),
            "fecha de publicación": dict(date=None),
            "tema": dict(category=None),
        }
        for what, broken in cases.items():
            with self.subTest(what=what):
                report, posts = self.run_sync(page(**broken))
                self.assertEqual(posts, [])
                self.assertEqual(report.created, 0)
                [(_, notion_id, reasons)] = report.rejected
                self.assertEqual(notion_id, "p1")
                self.assertEqual(len(reasons), 1)
                self.assertIn(what, reasons[0])

    def test_unreadable_date_skips_the_post(self):
        report, posts = self.run_sync(page(date="14/11/2026"))
        self.assertEqual(posts, [])
        self.assertIn("«14/11/2026» no se puede leer", report.rejected[0][2][0])

    def test_one_bad_post_does_not_stop_the_good_ones(self):
        report, posts = self.run_sync(
            page("p1", title="Bueno", slug="bueno"),
            page("p2", title="Levantar un servidor sin mirar", slug="servidor", date=None),
            page("p3", title="Otro bueno", slug="otro-bueno"),
        )
        self.assertEqual([p.slug for p in posts], ["bueno", "otro-bueno"])
        self.assertEqual(report.created, 2)
        self.assertEqual(report.rejected, [(
            "Levantar un servidor sin mirar", "p2",
            ["le falta la fecha de publicación (propiedad «Fecha Publicacion»)"],
        )])
        # queda registrado en sync_errors, como un post sin tema
        errors = [c.args[0] for c in self.db.add.call_args_list if type(c.args[0]).__name__ == "SyncError"]
        self.assertEqual([(e.notion_id, e.message) for e in errors],
                         [("p2", "le falta la fecha de publicación (propiedad «Fecha Publicacion»)")])
        self.db.commit.assert_called()

    def test_a_published_post_that_breaks_is_removed_like_one_without_topic(self):
        stored = Post(notion_id="p1", slug="un-post", title="Un post")
        report, _ = self.run_sync(page(date=None), existing=[stored])
        self.assertEqual(report.deleted, 1)
        self.assertEqual(len(report.rejected), 1)

    def test_a_missing_property_stops_the_sync_before_writing(self):
        with self.assertRaises(EsquemaNotionError) as raised:
            self.run_sync(page("p1", drop=["Fecha Publicacion"]), page("p2", slug="b", drop=["Fecha Publicacion"]))
        self.assertEqual(raised.exception.problems, [
            "La base de Notion no tiene la propiedad «Fecha Publicacion» (tipo Fecha). Creala con ese nombre exacto.",
        ])
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.execute.assert_not_called()

    def test_duplicate_slug_keeps_the_oldest_page(self):
        report, posts = self.run_sync(
            page("p-new", title="El nuevo", slug="mismo", created="2026-11-10T00:00:00.000Z"),
            page("p-old", title="El viejo", slug="mismo", created="2026-10-01T00:00:00.000Z"),
        )
        self.assertEqual([p.notion_id for p in posts], ["p-old"])
        [(title, notion_id, [reason])] = report.rejected
        self.assertEqual((title, notion_id), ("El nuevo", "p-new"))
        self.assertIn("mismo slug «mismo» que «El viejo» (p-old)", reason)
        self.assertIn("se creó antes en Notion", reason)

    def test_duplicate_slug_keeps_the_one_already_published(self):
        stored = Post(notion_id="p-pub", slug="mismo", title="Publicado",
                      synced_at=datetime(2026, 12, 1))  # sin cambios en Notion
        report, posts = self.run_sync(
            page("p-older", title="Más viejo", slug="mismo", created="2026-01-01T00:00:00.000Z"),
            page("p-pub", title="Publicado", slug="mismo", created="2026-06-01T00:00:00.000Z"),
            existing=[stored],
        )
        self.assertEqual(posts, [])            # el publicado no cambió: no se reescribe
        self.assertEqual((report.skipped, report.deleted), (1, 0))
        [(_, notion_id, [reason])] = report.rejected
        self.assertEqual(notion_id, "p-older")
        self.assertIn("ya estaba publicado con ese slug", reason)


class RequiredProperties(unittest.TestCase):
    def test_well_formed_post_has_no_problems(self):
        details = get_details_from_post(page(date="2026-11-14T10:30:00.000-03:00"))
        self.assertEqual(details["problems"], [])
        self.assertEqual(details["published_at"], datetime(2026, 11, 14, 10, 30))
        self.assertEqual((details["title"], details["slug"], details["category_name"]),
                         ("Un post", "un-post", "concurrencia"))

    def test_blank_title_counts_as_missing(self):
        self.assertEqual(get_details_from_post(page(title="   "))["problems"],
                         ["le falta el título (propiedad «Titulo»)"])

    def test_every_problem_is_listed(self):
        problems = get_details_from_post(page(title="", slug="", date=None, category=None))["problems"]
        self.assertEqual(len(problems), 4)

    def test_schema(self):
        self.assertEqual(schema_problems([]), [])
        self.assertEqual(schema_problems([page(), page("p2")]), [])
        self.assertEqual(schema_problems([page(drop=["slug", "categoria"])]), [
            "La base de Notion no tiene la propiedad «slug» (tipo Texto). Creala con ese nombre exacto.",
            "La base de Notion no tiene la propiedad «categoria» (tipo Selección). Creala con ese nombre exacto.",
        ])
        wrong = page()
        wrong["properties"]["Fecha Publicacion"] = {"type": "rich_text", "rich_text": []}
        self.assertEqual(schema_problems([wrong]), [
            "La propiedad «Fecha Publicacion» de Notion es de tipo Texto; tiene que ser de tipo Fecha.",
        ])


class SyncOutput(unittest.TestCase):
    """Lo que imprime `cli.py sync`."""

    def run_cli(self, **kwargs):
        with mock.patch("cli.SessionLocal"), mock.patch("cli.sync_posts", **kwargs):
            return CliRunner().invoke(cli.app, ["sync"])

    def test_skipped_posts_say_what_to_fix(self):
        report = SyncReport(created=2, rejected=[
            ("Levantar un servidor sin mirar", "abc", ["le falta la fecha de publicación (propiedad «Fecha Publicacion»)"]),
            ("", "def", ["le falta el título (propiedad «Titulo»)", "le falta el slug (propiedad «slug»)"]),
        ])
        result = self.run_cli(return_value=report)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("2 nuevos, 0 reconvertidos, 0 sin cambios, 0 borrados, 2 salteados.", result.output)
        self.assertIn("  «Levantar un servidor sin mirar» (abc): le falta la fecha de publicación "
                      "(propiedad «Fecha Publicacion»).", result.output)
        self.assertIn("  Post sin título (def): le falta el título (propiedad «Titulo»); "
                      "le falta el slug (propiedad «slug»).", result.output)

    def test_missing_property_stops_with_the_reason(self):
        error = EsquemaNotionError(["La base de Notion no tiene la propiedad «slug» (tipo Texto). Creala con ese nombre exacto."])
        result = self.run_cli(side_effect=error)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("No se cambió nada.", result.output)
        self.assertIn("no tiene la propiedad «slug»", result.output)


class ReservedTopics(unittest.TestCase):
    def test_collisions(self):
        names = ["concurrencia", "EN", "archive", "Archivo", "search.json", "static", "life"]
        self.assertEqual(
            reserved_topics(names),
            [("Archivo", "archivo"), ("EN", "en"), ("archive", "archive"), ("static", "static")],
        )


if __name__ == "__main__":
    unittest.main()
