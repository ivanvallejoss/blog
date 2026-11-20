"""
Pruebas del sitio en los dos idiomas: rutas, posts bajo el idioma
equivocado, índice de búsqueda, nombres de tema, switch, hreflang, estado
«sin posts en este idioma» y páginas de error.

Sin base: los selectores del router se reemplazan con versiones en memoria
que filtran por idioma como las de app/selectors.py.

    uv run python -m unittest
"""
import re
import unittest
import warnings
from unittest import mock

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from fastapi.testclient import TestClient

from app.database import get_db
from app.i18n import TOPIC_NAMES, lang_from_path, other_lang, topic_name
from app.main import app
from app.models.category import Category
from app.urls import PAGES, RESERVED_TOPIC_SLUGS, registration_order

from tests.test_web import make_post, no_db

ES = [
    make_post("Concurrencia sin miedo", "concurrencia-sin-miedo", "concurrencia", 14, featured=True),
    make_post("Un año escribiendo", "un-ano-escribiendo", "life", 10),
    make_post("Mudarse con una mochila", "mudarse", "life", 3),
]
EN = [
    make_post("Fearless concurrency", "fearless-concurrency", "concurrencia", 14, featured=True,
              lang="en", excerpt="A hand-written excerpt."),
    make_post("One design system", "one-design-system", "design system", 2, lang="en"),
]
ALL = ES + EN
CATEGORIES = {}
for _post in ALL:
    CATEGORIES.setdefault(_post.category.slug, _post.category)
    _post.category = CATEGORIES[_post.category.slug]
for _id, _cat in enumerate(CATEGORIES.values(), 1):
    _cat.id = _id
CATEGORIES["herramientas"] = Category(id=99, name="herramientas", slug="herramientas")


def in_lang(lang, category_id=None):
    return [
        p for p in sorted(ALL, key=lambda p: p.published_at, reverse=True)
        if p.lang == lang and (category_id is None or p.category.id == category_id)
    ]


def fake_tag_counts(db, lang):
    counts = {}
    for post in in_lang(lang):
        counts.setdefault(post.category.slug, [post.category, 0])[1] += 1
    return [{"name": c.name, "slug": c.slug, "count": n} for c, n in counts.values()]


def fake_years(db, lang, category_id=None):
    posts = in_lang(lang, category_id)
    return [{"year": 2026, "posts": posts}] if posts else []


def fake_post(db, category_slug, post_slug, lang):
    return next((p for p in in_lang(lang) if p.slug == post_slug and p.category.slug == category_slug), None)


FAKES = {
    "get_published_posts": lambda db, lang: sorted(in_lang(lang), key=lambda p: not p.featured),
    "get_recent_posts": lambda db, lang, limit=None: in_lang(lang)[:limit],
    "get_tag_counts": fake_tag_counts,
    "count_posts": lambda db, lang, category_id=None: len(in_lang(lang, category_id)),
    "get_posts_by_year": fake_years,
    "get_category_by_slug": lambda db, slug: CATEGORIES.get(slug),
    "get_post_by_slugs": fake_post,
    "get_next_post": lambda db, post: None,
}


class Client(unittest.TestCase):
    switch = False

    def setUp(self):
        app.dependency_overrides[get_db] = no_db
        self.addCleanup(app.dependency_overrides.clear)
        self.client = TestClient(app, raise_server_exceptions=False)
        patches = [mock.patch(f"app.routers.blog.{name}", side_effect=fake) for name, fake in FAKES.items()]
        patches.append(mock.patch("app.main.get_recent_posts", side_effect=FAKES["get_recent_posts"]))
        patches.append(mock.patch("app.templating.LANG_SWITCH_ENABLED", self.switch))
        patches.append(mock.patch("app.templating.BASE_URL", "https://blog.example"))
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def get(self, path, status=200):
        response = self.client.get(path)
        self.assertEqual(response.status_code, status, path)
        return response.text


class Helpers(unittest.TestCase):
    def test_lang_from_path(self):
        for path, lang in [("/", "es"), ("/archivo/", "es"), ("/en", "en"), ("/en/", "en"),
                           ("/en/archive/", "en"), ("/en/a/b/c/", "en"), ("/enfoque/", "es"),
                           ("/concurrencia/en/", "es")]:
            self.assertEqual(lang_from_path(path), lang, path)

    def test_other_lang(self):
        self.assertEqual(other_lang("es"), "en")
        self.assertEqual(other_lang("en"), "es")

    def test_topic_name_with_translation(self):
        cat = Category(name="concurrencia", slug="concurrencia")
        self.assertEqual(topic_name(cat, "en"), "concurrency")
        self.assertEqual(topic_name({"name": "concurrencia", "slug": "concurrencia"}, "en"), "concurrency")

    def test_topic_name_without_translation(self):
        cat = Category(name="Design System", slug="design-system")
        self.assertEqual(topic_name(cat, "en"), "Design System")
        self.assertEqual(topic_name(Category(name="concurrencia", slug="concurrencia"), "es"), "concurrencia")
        self.assertEqual(topic_name(cat, "pt"), "Design System")

    def test_topic_dictionary_is_by_language(self):
        self.assertEqual(set(TOPIC_NAMES), {"es", "en"})

    def test_fixed_routes_go_first(self):
        order = [path for _, _, path in registration_order()]
        fixed = [path for path in order if "{" not in path]
        self.assertEqual(order[:len(fixed)], fixed)
        self.assertLess(order.index("/en/{category_slug}/"), order.index("/{category_slug}/{post_slug}/"))

    def test_spanish_urls_did_not_change(self):
        self.assertEqual({name: paths["es"] for name, paths in PAGES.items()}, {
            "post_list": "/", "archive": "/archivo/",
            "get_category": "/{category_slug}/", "get_post": "/{category_slug}/{post_slug}/",
        })

    def test_reserved_slugs(self):
        self.assertTrue({"en", "archivo", "archive", "search.json"} <= RESERVED_TOPIC_SLUGS)


class Summary(unittest.TestCase):
    def test_excerpt_wins(self):
        self.assertEqual(EN[0].summary, "A hand-written excerpt.")

    def test_derived_without_excerpt(self):
        self.assertEqual(EN[1].summary, "Bajada de One design system.")
        blank = make_post("X", "x", "life", 1, excerpt="   ")
        self.assertEqual(blank.summary, "Bajada de X.")


class Routes(Client):
    def test_eight_routes(self):
        for path in ["/", "/archivo/", "/concurrencia/", "/concurrencia/concurrencia-sin-miedo/",
                     "/en/", "/en/archive/", "/en/concurrencia/", "/en/concurrencia/fearless-concurrency/"]:
            html = self.get(path)
            lang = "en" if path.startswith("/en/") else "es"
            self.assertIn(f'<html lang="{lang}">', html, path)

    def test_english_pages_show_english_content(self):
        home = self.get("/en/")
        self.assertIn("Fearless concurrency", home)
        self.assertNotIn("Concurrencia sin miedo", home)
        self.assertIn("A hand-written excerpt.", home)
        self.assertIn(">Featured<", home)
        self.assertIn("14 NOV · concurrency · 2 min", re.sub(r"<[^>]+>", "", home))
        self.assertIn('href="/en/concurrencia/fearless-concurrency/"', home)
        self.assertIn('href="/en/archive/"', home)

    def test_spanish_home_is_unchanged(self):
        home = self.get("/")
        self.assertIn("Concurrencia sin miedo", home)
        self.assertNotIn("Fearless", home)
        self.assertIn("14 NOV · concurrencia · 2 min", re.sub(r"<[^>]+>", "", home))
        self.assertIn('href="/archivo/"', home)

    def test_english_archive(self):
        html = self.get("/en/archive/")
        self.assertIn(">Archive<", html)
        self.assertIn("2 posts · 2 topics", html)
        # Filtros con el nombre traducido y rutas bajo /en/ (HTMX empuja esa URL).
        self.assertIn('hx-get="/en/concurrencia/"', html)
        self.assertRegex(html, r'archive-filter__name">concurrency<')
        self.assertIn('archive-row__cat">concurrency<', html)

    def test_english_topic(self):
        html = self.get("/en/concurrencia/")
        self.assertIn("<title>concurrency — Archive", html)
        self.assertIn('aria-current="page"', html)

    def test_english_post(self):
        html = self.get("/en/concurrencia/fearless-concurrency/")
        self.assertIn("14 NOV 2026", html)
        self.assertIn('article__tag hit" href="/en/concurrencia/">concurrency<', html)
        self.assertIn('aria-label="Reading options"', html)

    def test_post_under_the_wrong_language_is_404(self):
        html = self.get("/en/concurrencia/concurrencia-sin-miedo/", 404)
        self.assertIn("The post you&#39;re looking for doesn&#39;t exist or was moved.", html)
        html = self.get("/concurrencia/fearless-concurrency/", 404)
        self.assertIn("El post que buscás no existe o fue movido.", html)

    def test_archive_is_not_a_topic(self):
        with mock.patch("app.routers.blog.get_category_by_slug") as category:
            self.get("/en/archive/")
            self.get("/archivo/")
        category.assert_not_called()

    def test_unknown_topic_is_404_in_both(self):
        self.get("/no-existe/", 404)
        self.get("/en/no-existe/", 404)


class SearchByLang(Client):
    def test_index_per_language(self):
        en = self.client.get("/search.json?lang=en").json()
        self.assertEqual([e["slug"] for e in en], ["fearless-concurrency", "one-design-system"])
        self.assertEqual({e["lang"] for e in en}, {"en"})
        self.assertEqual(en[0]["url"], "/en/concurrencia/fearless-concurrency/")
        self.assertEqual(en[0]["category"], "concurrency")
        self.assertEqual(en[0]["category_slug"], "concurrencia")
        self.assertEqual(en[0]["meta_label"], "14 NOV · concurrency · 2 min")
        es = self.client.get("/search.json?lang=es").json()
        self.assertEqual({e["lang"] for e in es}, {"es"})
        self.assertEqual(es[0]["category"], "concurrencia")
        self.assertEqual(self.client.get("/search.json").json(), es)

    def test_search_dialog_asks_for_the_page_language(self):
        self.assertIn('data-index-url="/search.json?lang=en"', self.get("/en/"))
        self.assertIn('data-index-url="/search.json?lang=es"', self.get("/"))


class EmptyByLanguage(Client):
    def test_topic_only_in_spanish(self):
        html = self.get("/en/life/")
        self.assertIn("No posts in English here yet", html)
        self.assertIn("There are 2 posts on <em>life</em> in Spanish.", html)
        self.assertIn('href="/life/" hreflang="es" lang="es">Ver en español<', html)

    def test_topic_only_in_english(self):
        html = self.get("/design-system/")
        self.assertIn("Todavía no hay posts en español acá", html)
        self.assertIn("Hay 1 post sobre <em>design system</em> en inglés.", html)
        self.assertIn('href="/en/design-system/" hreflang="en" lang="en">See in English<', html)

    def test_topic_without_posts_in_either(self):
        html = self.get("/en/herramientas/")
        self.assertIn("No posts on this topic yet", html)
        self.assertNotIn("in Spanish", html)

    def test_home_and_archive_without_posts_in_the_language(self):
        global ALL
        saved = ALL
        ALL = ES
        try:
            for path in ["/en/", "/en/archive/"]:
                html = self.get(path)
                self.assertIn("There are 3 posts in Spanish.", html)
                self.assertIn(f'href="{"/" if path == "/en/" else "/archivo/"}" hreflang="es"', html)
            ALL = []
            self.assertIn("No posts published yet.", self.get("/en/"))
            self.assertNotIn("in Spanish", self.get("/en/archive/"))
        finally:
            ALL = saved


class ErrorPages(Client):
    def test_404_under_en_is_english(self):
        html = self.get("/en/a/b/c/", 404)
        self.assertIn('<html lang="en">', html)
        self.assertIn("Page not found", html)
        self.assertIn("Maybe you were looking for", html)
        self.assertIn('href="/en/concurrencia/fearless-concurrency/"', html)
        self.assertNotIn("Concurrencia sin miedo", html)
        self.assertIn('href="/en/">Back to home', html)

    def test_unknown_english_topic(self):
        html = self.get("/en/no-existe/", 404)
        self.assertIn("The page you&#39;re looking for doesn&#39;t exist or was moved.", html)

    def test_404_in_spanish(self):
        html = self.get("/no/existe/del/todo/", 404)
        self.assertIn('<html lang="es">', html)
        self.assertIn("Página no encontrada", html)

    def test_generic_error_under_en(self):
        with self.assertLogs("blog.errors", "WARNING"):
            response = self.client.post("/en/")
        self.assertEqual(response.status_code, 405)
        self.assertIn('<html lang="en">', response.text)
        self.assertIn("Something went wrong", response.text)
        self.assertIn('href="/en/">Back to home', response.text)


class Alternates(Client):
    def hreflang(self, html):
        return re.findall(r'<link rel="alternate" hreflang="([\w-]+)" href="([^"]+)">', html)

    def test_pages_with_an_equivalent(self):
        self.assertEqual(self.hreflang(self.get("/en/archive/")), [
            ("es", "https://blog.example/archivo/"),
            ("en", "https://blog.example/en/archive/"),
            ("x-default", "https://blog.example/archivo/"),
        ])
        self.assertEqual(len(self.hreflang(self.get("/"))), 3)
        self.assertIn(("en", "https://blog.example/en/life/"), self.hreflang(self.get("/life/")))

    def test_posts_and_errors_have_none(self):
        self.assertEqual(self.hreflang(self.get("/concurrencia/concurrencia-sin-miedo/")), [])
        self.assertEqual(self.hreflang(self.get("/en/no-existe/", 404)), [])

    def test_switch_hidden_by_default(self):
        self.assertNotIn('class="lang-switch"', self.get("/"))


class Switch(Client):
    switch = True

    def links(self, html):
        block = re.search(r'<div id="lang-switch".*?</div>', html, re.S).group(0)
        return {
            code: (href, "aria-current" in tag)
            for tag, href, code in re.findall(r'(<a [^>]*href="([^"]+)" hreflang="(\w+)"[^>]*>)', block)
        }

    def test_equivalent_pages(self):
        self.assertEqual(self.links(self.get("/")), {"es": ("/", True), "en": ("/en/", False)})
        self.assertEqual(self.links(self.get("/en/archive/")), {"es": ("/archivo/", False), "en": ("/en/archive/", True)})
        self.assertEqual(self.links(self.get("/life/")), {"es": ("/life/", True), "en": ("/en/life/", False)})

    def test_post_goes_to_the_other_home(self):
        self.assertEqual(
            self.links(self.get("/en/concurrencia/fearless-concurrency/")),
            {"es": ("/", False), "en": ("/en/", True)},
        )

    def test_error_page_goes_to_the_other_home(self):
        self.assertEqual(self.links(self.get("/en/no-existe/", 404)), {"es": ("/", False), "en": ("/en/", True)})
        self.assertEqual(self.links(self.get("/concurrencia/nope/", 404)), {"es": ("/", True), "en": ("/en/", False)})

    def test_links_are_real_and_labelled(self):
        html = self.get("/en/")
        self.assertIn('lang="es"', html)
        self.assertRegex(html, r'aria-label="Español"[^>]*>ES</a>')
        self.assertRegex(html, r'aria-label="English" aria-current="true"[^>]*>EN</a>')
        self.assertNotIn("<button type=\"button\" class=\"lang-switch", html)

    def test_archive_filters_bring_the_switch_back(self):
        self.assertIn('hx-select-oob="#archive-filters,#lang-switch"', self.get("/en/archive/"))


if __name__ == "__main__":
    unittest.main()
