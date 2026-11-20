"""
Pruebas de /search.json y de los manejadores de error, con el cliente de
pruebas de FastAPI. No tocan la base: los selectores se reemplazan con posts
armados en memoria y la sesión con None.

    uv run python -m unittest
"""
import re
import unittest
import warnings
from datetime import datetime
from unittest import mock

with warnings.catch_warnings():
    warnings.simplefilter("ignore")  # aviso de Starlette sobre httpx: no es de este repo
    from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models.category import Category
from app.models.post import Post
from app.search import build_search_index


def make_post(title, slug, category, day, minutes_words=400, featured=False, lang="es", excerpt=None):
    cat = Category(name=category, slug=category.replace(" ", "-"))
    body = f"Bajada de {title}.\n\n" + "palabra " * minutes_words
    return Post(
        title=title, slug=slug, content_markdown=body, content_html="", content_toc=[],
        published_at=datetime(2026, 11, day, 10, 0), featured=featured, category=cat,
        lang=lang, excerpt=excerpt,
    )


POSTS = [
    make_post("Concurrencia sin miedo", "concurrencia-sin-miedo", "concurrencia", 14),
    make_post("Un design system", "un-design-system", "design system", 2),
]


def no_db():
    yield None


class SearchIndex(unittest.TestCase):
    def test_entry_has_what_the_client_paints(self):
        index = build_search_index(POSTS, "es", lambda p: f"/{p.category.slug}/{p.slug}/")
        self.assertEqual(index[0], {
            "title": "Concurrencia sin miedo",
            "slug": "concurrencia-sin-miedo",
            "category": "concurrencia",
            "category_slug": "concurrencia",
            "excerpt": "Bajada de Concurrencia sin miedo.",
            "published_at": "2026-11-14",
            "reading_minutes": 2,
            "lang": "es",
            "url": "/concurrencia/concurrencia-sin-miedo/",
            "date_label": "14 NOV",
            "meta_label": "14 NOV · concurrencia · 2 min",
        })

    def test_other_language_posts_are_left_out(self):
        self.assertEqual(build_search_index(POSTS, "en", lambda p: "/"), [])


class Web(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_db] = no_db
        self.client = TestClient(app, raise_server_exceptions=False)
        # La 404 consulta la base para «Quizás buscabas»: acá, posts en memoria.
        patcher = mock.patch("app.main.get_recent_posts", return_value=POSTS)
        self.recent = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        app.dependency_overrides.clear()

    # — /search.json —

    def test_search_json(self):
        with mock.patch("app.routers.blog.get_recent_posts", return_value=POSTS):
            response = self.client.get("/search.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertIn("max-age=", response.headers["cache-control"])
        data = response.json()
        self.assertEqual([entry["slug"] for entry in data], ["concurrencia-sin-miedo", "un-design-system"])
        # La ruta sola, sin host: no depende de las cabeceras del proxy.
        self.assertEqual(data[1]["url"], "/design-system/un-design-system/")

    def test_search_json_lang(self):
        with mock.patch("app.routers.blog.get_recent_posts", return_value=POSTS) as recent:
            self.assertEqual(self.client.get("/search.json?lang=en").json(), [])
            self.assertEqual(recent.call_args.args[1], "en")
            # Un idioma desconocido cae en español.
            self.assertEqual(len(self.client.get("/search.json?lang=xx").json()), 2)
            self.assertEqual(recent.call_args.args[1], "es")

    def test_search_json_is_not_a_topic(self):
        # Registrada antes que /{category_slug}/: «search.json» no se busca como tema.
        with mock.patch("app.routers.blog.get_recent_posts", return_value=[]), \
             mock.patch("app.routers.blog.get_category_by_slug") as category:
            self.client.get("/search.json")
        category.assert_not_called()

    # — 404 —

    def assert_404_page(self, response, body):
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers["content-type"].startswith("text/html"))
        self.assertIn('class="cmyk-num error-page__number"', response.text)
        self.assertIn(f'error-page__body">{body}<', response.text)

    def test_unknown_one_segment(self):
        with mock.patch("app.routers.blog.get_category_by_slug", return_value=None):
            response = self.client.get("/no-existe/")
        self.assert_404_page(response, "El contenido que buscás no existe o fue movido.")

    def test_unknown_post(self):
        with mock.patch("app.routers.blog.get_post_by_slugs", return_value=None):
            response = self.client.get("/concurrencia/no-existe/")
        self.assert_404_page(response, "El post que buscás no existe o fue movido.")

    def test_three_segments_is_html_not_json(self):
        response = self.client.get("/a/b/c/")
        self.assert_404_page(response, "El contenido que buscás no existe o fue movido.")
        self.assertNotIn('"detail"', response.text)

    def test_404_lists_recent_posts(self):
        response = self.client.get("/a/b/c/")
        self.assertIn("Quizás buscabas", response.text)
        self.assertIn('href="/concurrencia/concurrencia-sin-miedo/"', response.text)

    def test_404_without_database(self):
        self.recent.side_effect = RuntimeError("la base no responde")
        with self.assertLogs("blog.errors", "WARNING"):
            response = self.client.get("/a/b/c/")
        self.assert_404_page(response, "El contenido que buscás no existe o fue movido.")
        self.assertNotIn("Quizás buscabas", response.text)
        self.assertIn("Volver al inicio", response.text)

    def test_plates_are_hidden_from_assistive_tech(self):
        html = self.client.get("/a/b/c/").text
        self.assertEqual(html.count('class="plate plate-'), 3)
        self.assertEqual(len(re.findall(r'class="plate plate-[cmy]" aria-hidden="true"', html)), 3)

    def test_no_absolute_internal_links(self):
        html = self.client.get("/a/b/c/").text
        self.assertNotRegex(html, r'(href|src|hx-get)="https?://testserver')

    # — share_url —

    def post_page(self):
        post = POSTS[0]
        post.content_toc = []
        with mock.patch("app.routers.blog.get_post_by_slugs", return_value=post), \
             mock.patch("app.routers.blog.get_next_post", return_value=POSTS[1]):
            return self.client.get("/concurrencia/concurrencia-sin-miedo/").text

    def test_share_url_from_the_request_without_base_url(self):
        with mock.patch("app.templating.BASE_URL", None):
            html = self.post_page()
        self.assertIn("share-offsite/?url=http%3A//testserver/concurrencia/concurrencia-sin-miedo/", html)

    def test_share_url_from_base_url(self):
        with mock.patch("app.templating.BASE_URL", "https://blog.ivanvallejos.dev"):
            html = self.post_page()
        self.assertIn("share-offsite/?url=https%3A//blog.ivanvallejos.dev/concurrencia/concurrencia-sin-miedo/", html)
        # «Siguiente» sigue siendo solo la ruta.
        self.assertIn('href="/design-system/un-design-system/" rel="next"', html)

    # — 500 y genérico —

    def test_unhandled_exception_is_500_with_reference(self):
        @app.get("/__boom__/x/y/")
        def boom():
            raise RuntimeError("falla de prueba")
        app.router.routes.insert(0, app.router.routes.pop())
        self.addCleanup(lambda: app.router.routes.pop(0))

        with self.assertLogs("blog.errors", "ERROR") as logs:
            response = self.client.get("/__boom__/x/y/?a=1")
        self.assertEqual(response.status_code, 500)
        self.assertIn("Algo salió mal", response.text)
        ref = re.search(r'error-page__ref">ref · ([0-9a-f]{4}-\d{2}[a-z]{3}-\d{4})<', response.text).group(1)
        self.assertIn(ref, logs.output[0])
        self.assertIn("RuntimeError: falla de prueba", logs.output[0])  # con la traza
        # «Reintentar» funciona sin JavaScript: un link a la misma URL.
        self.assertIn('href="/__boom__/x/y/?a=1"', response.text)
        # La búsqueda depende de la base: la 500 no la ofrece.
        self.assertNotIn("data-search-open", response.text)

    def test_other_status_uses_generic_page(self):
        with self.assertLogs("blog.errors", "WARNING"):
            response = self.client.post("/")
        self.assertEqual(response.status_code, 405)
        self.assertIn("Algo salió mal", response.text)
        self.assertIn("error-page__ref", response.text)
        self.assertIn("allow", response.headers)


if __name__ == "__main__":
    unittest.main()
