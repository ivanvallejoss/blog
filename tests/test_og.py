"""
Pruebas de las imágenes para compartir (app/og): colores, anillo, partido de
líneas del título, y cuándo se generan y se borran. Dibujan de verdad, en una
carpeta temporal; no tocan static/og ni la base.

    uv run python -m unittest
"""
import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from PIL import Image

from app.models.category import Category
from app.models.post import Post
from app.og import draw, images, tokens
from sync.services import sync_posts


def og_post(title="Concurrencia sin miedo", slug="concurrencia-sin-miedo", lang="es", words=400, day=14):
    return Post(
        title=title, slug=slug, lang=lang, content_markdown="Hola.\n\n" + "palabra " * words,
        content_html="", content_toc=[], published_at=datetime(2026, 11, day, 10, 0),
        category=Category(name="concurrencia", slug="concurrencia"), notion_id=f"n-{slug}",
    )


TITLE_100 = "Cómo diseñé un sistema de sincronización entre Notion y PostgreSQL sin perder la calma por el camino"


class Tokens(unittest.TestCase):
    def test_oklch_matches_what_chromium_paints(self):
        # Medidos en la captura del prototipo (Chromium) y en el favicon.
        self.assertEqual(tokens.BRAND_RING, (225, 144, 31))
        self.assertEqual(tokens.BRAND_RING_SMALL, (213, 130, 7))

    def test_ring_paths_are_the_favicon_paths(self):
        svg = Path("static/public/favicon.svg").read_text()
        self.assertEqual(tuple(re.findall(r'd="([^"]+)"', svg)), tokens.RING_PATHS)

    def test_ring_arcs_leave_the_bottom_right_quarter_open(self):
        arcs = draw.ring_arcs()
        self.assertEqual(len(arcs), 3)
        for start, end in arcs:
            self.assertGreater(end, start)
        self.assertAlmostEqual(arcs[0][0], 90, places=1)
        self.assertAlmostEqual(arcs[2][1], 360, places=1)


class Wrapping(unittest.TestCase):
    style = draw.title_style(64)

    def words(self, text):
        return [[(word, self.style)] for word in text.split()]

    def widths(self, lines):
        space = draw.advance(" ", self.style)
        return [draw._line_width(line, space) for line in lines]

    def test_balance_keeps_the_line_count_and_evens_the_lines(self):
        words, space = self.words(TITLE_100), draw.advance(" ", self.style)
        greedy = draw.wrap(words, 960, space)
        balanced = draw.balance(words, 960, space)
        self.assertEqual(len(balanced), len(greedy))
        self.assertLessEqual(max(self.widths(balanced)), 960)
        spread = lambda lines: max(self.widths(lines)) - min(self.widths(lines))
        self.assertLess(spread(balanced), spread(greedy))
        # el texto no cambia: solo dónde se corta
        flat = " ".join(" ".join(t for t, _ in word) for line in balanced for word in line)
        self.assertEqual(flat, TITLE_100)

    def test_one_line_stays_one_line(self):
        words = self.words("Hola mundo")
        self.assertEqual(len(draw.balance(words, 960, draw.advance(" ", self.style))), 1)

    def test_a_word_wider_than_the_column_is_cut(self):
        words = self.words("W" * 60)
        lines = draw.balance(words, 960, draw.advance(" ", self.style))
        self.assertGreater(len(lines), 1)
        self.assertLessEqual(max(self.widths(lines)), 960)

    def test_emphasis_in_the_default_phrase(self):
        roman = draw.Style("serif", 36, (0, 0, 0))
        italic = draw.Style("serif-italic", 36, (0, 0, 0))
        words = draw.rich_words("sobre *concurrencia*, sistemas", roman, italic)
        self.assertEqual(words, [
            [("sobre", roman)],
            [("concurrencia", italic), (",", roman)],
            [("sistemas", roman)],
        ])


class TitleLayout(unittest.TestCase):
    def ceiling(self):
        return tokens.OG_PAD_Y + draw.brand_row_height() + tokens.TITLE_CLEARANCE

    def test_short_title_uses_the_large_size(self):
        layout = draw.layout_title("Concurrencia sin miedo: async en Python 3.14")
        self.assertEqual(layout.size, tokens.TITLE_SIZE)
        self.assertEqual(layout.lines, ["Concurrencia sin miedo:", "async en Python 3.14"])

    def test_long_title_uses_the_reduced_size(self):
        title = "Un título que pasa de los sesenta caracteres para ver si se achica"
        self.assertGreater(len(title), tokens.TITLE_LONG_AFTER)
        self.assertEqual(draw.layout_title(title).size, tokens.TITLE_SIZE_LONG)

    def test_100_characters_fit_without_touching_the_rows(self):
        self.assertEqual(len(TITLE_100), 100)  # el máximo de Post.title
        layout = draw.layout_title(TITLE_100)
        style = draw.title_style(layout.size)
        self.assertEqual(layout.size, tokens.TITLE_SIZE_LONG)
        # no pisa la fila de abajo: el bloque termina 36 px antes de la fila de autor
        meta_top = tokens.OG_HEIGHT - tokens.OG_PAD_Y - tokens.META_SIZE * tokens.BODY_LEADING
        bottom = layout.top + len(layout.lines) * style.line_height
        self.assertAlmostEqual(bottom, meta_top - tokens.TITLE_MARGIN_BOTTOM)
        # no se sale: cada línea entra en 960 px y el tema queda debajo de la marca
        for line in layout.lines:
            self.assertLessEqual(draw.advance(line, style), tokens.TITLE_MAX_WIDTH)
        self.assertGreaterEqual(layout.topic_top, self.ceiling())

    def test_a_title_that_cannot_fit_shrinks(self):
        layout = draw.layout_title("W" * 100)
        self.assertLess(layout.size, tokens.TITLE_SIZE_LONG)
        self.assertGreaterEqual(layout.topic_top, self.ceiling())

    def test_post_card_size(self):
        card = draw.post_card(title=TITLE_100, topic="año", meta="Iván · 14 NOV 2026 · 9 min",
                              domain="blog.example", mark="IV", sub="/blog")
        self.assertEqual(card.size, (1200, 630))


class Generation(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name) / "og"
        for patcher in (mock.patch.object(images, "OG_DIR", self.dir),
                        mock.patch("app.config.BASE_URL", "https://blog.example")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_first_pass_writes_defaults_and_posts(self):
        report = images.refresh_images([og_post(), og_post("Fearless", "fearless", lang="en")])
        self.assertEqual((report.generated, report.defaults, report.failed), (2, 2, []))
        for path in ("concurrencia-sin-miedo.png", "fearless.png", "default/es.png", "default/en.png"):
            with Image.open(self.dir / path) as image:
                self.assertEqual(image.size, (1200, 630))

    def test_regenerates_only_when_what_it_shows_changes(self):
        post = og_post()
        images.refresh_images([post])
        self.assertEqual(images.refresh_images([post]).unchanged, 1)

        post.content_html = "<p>otro html</p>"      # no se ve en la imagen
        post.excerpt = "Otra bajada"
        post.featured = True
        self.assertEqual(images.refresh_images([post]).generated, 0)

        changes = (
            lambda p: setattr(p, "title", "Otro título"),
            lambda p: setattr(p, "published_at", datetime(2026, 11, 15)),
            lambda p: setattr(p, "content_markdown", "palabra " * 2000),   # minutos
            lambda p: setattr(p, "category", Category(name="vida", slug="vida")),
        )
        for change in changes:
            change(post)
            self.assertEqual(images.refresh_images([post]).generated, 1)
            self.assertEqual(images.refresh_images([post]).generated, 0)

    def test_language_and_domain_are_part_of_the_image(self):
        post = og_post()
        images.refresh_images([post])
        post.lang = "en"                    # fecha y tema en inglés
        self.assertEqual(images.refresh_images([post]).generated, 1)
        with mock.patch("app.config.BASE_URL", "https://otro.example"):
            self.assertEqual(images.refresh_images([post]).generated, 1)

    def test_force_regenerates_everything(self):
        post = og_post()
        images.refresh_images([post])
        report = images.refresh_images([post], force=True)
        self.assertEqual((report.generated, report.defaults), (1, 2))

    def test_the_url_version_is_the_fingerprint(self):
        post = og_post()
        path = images.post_image_path(post.slug)
        self.assertIsNone(images.image_version(path))
        images.refresh_images([post])
        version = images.image_version(path)
        self.assertEqual(version, images.fingerprint(images.post_fields(post)))
        post.title = "Otro"
        images.refresh_images([post])
        self.assertNotEqual(images.image_version(path), version)

    def test_removed_slugs_and_prune(self):
        keep, gone = og_post(), og_post("Viejo", "viejo")
        images.refresh_images([keep, gone])
        report = images.refresh_images([keep], removed_slugs=["viejo"])
        self.assertEqual(report.removed, 1)
        self.assertFalse((self.dir / "viejo.png").exists())

        images.refresh_images([gone])                       # resto de otra pasada
        report = images.refresh_images([keep], prune=True)
        self.assertFalse((self.dir / "viejo.png").exists())
        self.assertTrue((self.dir / "concurrencia-sin-miedo.png").exists())
        self.assertTrue((self.dir / "default" / "es.png").exists())

    def test_a_failure_does_not_stop_the_pass_and_drops_the_stale_image(self):
        broken, fine = og_post("Roto", "roto"), og_post()
        images.refresh_images([broken])
        broken.title = "Roto otra vez"
        real = draw.post_card

        def post_card(**fields):
            if fields["title"].startswith("Roto"):
                raise RuntimeError("sin fuente")
            return real(**fields)

        with mock.patch.object(draw, "post_card", side_effect=post_card), \
             mock.patch.object(images.logger, "exception"):
            report = images.refresh_images([broken, fine])
        self.assertEqual(report.generated, 1)
        self.assertEqual(report.failed, [("Roto otra vez", "roto", "sin fuente")])
        self.assertFalse((self.dir / "roto.png").exists())  # usa la por defecto


class SyncImages(unittest.TestCase):
    """El sync borra la imagen de un post que ya no está en Notion, o que cambió de slug."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name) / "og"
        for patcher in (mock.patch.object(images, "OG_DIR", self.dir),
                        mock.patch("sync.services.logger")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def db_with(self, existing, after):
        def query(model):
            q = mock.MagicMock()
            q.all.return_value = existing if model is Post else []
            q.options.return_value.all.return_value = after
            return q
        db = mock.MagicMock()
        db.query.side_effect = query
        return db

    def test_deleting_a_post_deletes_its_image(self):
        gone = og_post("Borrado", "borrado")
        images.refresh_images([gone])
        self.assertTrue((self.dir / "borrado.png").exists())

        with mock.patch("sync.services.get_posts", return_value=[]):
            report = sync_posts(self.db_with([gone], after=[]))
        self.assertEqual(report.deleted, 1)
        self.assertEqual(report.images.removed, 1)
        self.assertFalse((self.dir / "borrado.png").exists())

    def test_unchanged_post_keeps_its_image(self):
        post = og_post()
        images.refresh_images([post])
        before = (self.dir / "concurrencia-sin-miedo.png").stat().st_mtime_ns
        notion = {"notion_id": post.notion_id, "title": post.title, "category_name": "concurrencia",
                  "synced_at": datetime(2026, 1, 1), "lang_unknown": None}
        post.synced_at = datetime(2026, 1, 2)   # Notion no cambió desde el último sync
        with mock.patch("sync.services.get_posts", return_value=[{}]), \
             mock.patch("sync.services.get_details_from_post", return_value=notion):
            report = sync_posts(self.db_with([post], after=[post]))
        self.assertEqual((report.skipped, report.images.unchanged, report.images.generated), (1, 1, 0))
        self.assertEqual((self.dir / "concurrencia-sin-miedo.png").stat().st_mtime_ns, before)


class TouchIcon(unittest.TestCase):
    def test_committed_icon_is_what_the_code_draws(self):
        with Image.open("static/public/apple-touch-icon.png") as committed:
            self.assertEqual(committed.size, (180, 180))
            self.assertEqual(committed.convert("RGB").tobytes(), draw.touch_icon().tobytes())


if __name__ == "__main__":
    unittest.main()
