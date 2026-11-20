"""
Pruebas de lo que sale del sitio para compartir: las meta tags de cada tipo de
página en los dos idiomas (y su ausencia en las de error) y los feeds Atom.

Sin base: usan los selectores en memoria de tests/test_lang.py, con
BLOG_BASE_URL en https://blog.example.

    uv run python -m unittest
"""
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from unittest import mock

from app.feed import FEED_LIMIT, build_feed, feed_html
from app.og import images
from tests.test_lang import ALL, CATEGORIES, Client, make_post

BASE = "https://blog.example"
ATOM = {"a": "http://www.w3.org/2005/Atom"}

# Un post con lo que el feed tiene que reescribir: el ancla «#» de los títulos,
# un link a otra página del sitio, uno a una sección del mismo post, una
# imagen con ruta relativa y un link externo, que no se toca.
RICH_HTML = (
    '<h2 id="el-loop">El loop<a class="headerlink" href="#el-loop" title="Enlace a esta sección">#</a></h2>\n'
    '<p>Ver <a href="/archivo/">el archivo</a>, <a href="#el-loop">la sección</a>, '
    '<img alt="x" src="/static/public/favicon.svg"> y <a href="https://docs.python.org/3/?a=1&amp;b=2">docs</a>.</p>'
)
RICH_POST = next(p for p in ALL if p.slug == "concurrencia-sin-miedo")


def metas(html: str) -> dict[str, list[str]]:
    """{nombre o propiedad: [contenidos]} de las meta tags y el canonical de una página."""
    found: dict[str, list[str]] = {}
    for key, value in re.findall(r'<meta (?:name|property)="([^"]+)" content="([^"]*)"', html):
        found.setdefault(key, []).append(value)
    for value in re.findall(r'<link rel="canonical" href="([^"]+)"', html):
        found.setdefault("canonical", []).append(value)
    return found


class ShareClient(Client):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.og_dir = Path(tmp.name)
        for patcher in (mock.patch.object(images, "OG_DIR", self.og_dir),
                        mock.patch("app.config.BASE_URL", BASE),
                        mock.patch.object(RICH_POST, "content_html", RICH_HTML)):
            patcher.start()
            self.addCleanup(patcher.stop)


class ListingMeta(ShareClient):
    PAGES = {
        # ruta: (idioma, título, descripción)
        "/": ("es", "blog — Iván Vallejos", "Notas de Iván Vallejos sobre concurrencia, sistemas de diseño y la vida alrededor del código."),
        "/en/": ("en", "blog — Iván Vallejos", "Notes by Iván Vallejos on concurrency, design systems and the life around code."),
        "/archivo/": ("es", "Archivo", "Todos los posts del blog, por año y por tema."),
        "/en/archive/": ("en", "Archive", "Every post on the blog, by year and by topic."),
        "/concurrencia/": ("es", "concurrencia — Archivo", "Posts sobre concurrencia en el blog de Iván Vallejos."),
        "/en/concurrencia/": ("en", "concurrency — Archive", "Posts about concurrency on Iván Vallejos’s blog."),
    }
    LOCALE = {"es": ("es_AR", "en_US"), "en": ("en_US", "es_AR")}

    def test_home_archive_and_topic_in_both_languages(self):
        for path, (lang, title, description) in self.PAGES.items():
            with self.subTest(path=path):
                m = metas(self.get(path))
                locale, alternate = self.LOCALE[lang]
                self.assertEqual(m["og:type"], ["website"])
                self.assertEqual(m["description"], [description])
                self.assertEqual(m["og:description"], [description])
                self.assertEqual(m["og:title"], [title])
                self.assertEqual(m["canonical"], [BASE + path])
                self.assertEqual(m["og:url"], [BASE + path])
                self.assertEqual(m["og:locale"], [locale])
                self.assertEqual(m["og:locale:alternate"], [alternate])
                self.assertEqual(m["og:site_name"], ["blog — Iván Vallejos"])
                self.assertEqual(m["twitter:card"], ["summary_large_image"])
                [image] = m["og:image"]
                self.assertRegex(image, rf"^{BASE}/static/og/default/{lang}\.png\?v=[0-9a-f]{{12}}$")
                self.assertEqual((m["og:image:width"], m["og:image:height"]), (["1200"], ["630"]))
                self.assertTrue(m["og:image:alt"][0].startswith("IV/blog: "))
                self.assertNotIn("article:published_time", m)

    def test_default_image_version_follows_the_phrase(self):
        es = metas(self.get("/"))["og:image"][0]
        en = metas(self.get("/en/"))["og:image"][0]
        self.assertNotEqual(es.split("?v=")[1], en.split("?v=")[1])


class PostMeta(ShareClient):
    ES = "/concurrencia/concurrencia-sin-miedo/"
    EN = "/en/concurrencia/fearless-concurrency/"

    def post(self, slug):
        return next(p for p in ALL if p.slug == slug)

    def test_post_without_its_image_uses_the_default_of_its_language(self):
        for path, lang in ((self.ES, "es"), (self.EN, "en")):
            with self.subTest(path=path):
                m = metas(self.get(path))
                self.assertRegex(m["og:image"][0], rf"^{BASE}/static/og/default/{lang}\.png\?v=")

    def test_post_in_both_languages(self):
        with mock.patch("app.config.BASE_URL", BASE):
            images.refresh_images([self.post("concurrencia-sin-miedo"), self.post("fearless-concurrency")])
        cases = (
            (self.ES, "concurrencia-sin-miedo", "es_AR", "Concurrencia sin miedo",
             "Bajada de Concurrencia sin miedo.", "«Concurrencia sin miedo», en IV/blog"),
            (self.EN, "fearless-concurrency", "en_US", "Fearless concurrency",
             "A hand-written excerpt.", "“Fearless concurrency”, on IV/blog"),
        )
        for path, slug, locale, title, description, alt in cases:
            with self.subTest(path=path):
                m = metas(self.get(path))
                self.assertEqual(m["og:type"], ["article"])
                self.assertEqual(m["og:title"], [title])
                self.assertEqual(m["description"], [description])  # Post.summary
                self.assertEqual(m["og:description"], [description])
                self.assertEqual(m["canonical"], [BASE + path])
                self.assertEqual(m["og:locale"], [locale])
                self.assertNotIn("og:locale:alternate", m)
                self.assertEqual(m["article:published_time"], ["2026-11-14T10:00:00Z"])
                version = images.image_version(images.post_image_path(slug))
                self.assertEqual(m["og:image"], [f"{BASE}/static/og/{slug}.png?v={version}"])
                self.assertEqual(m["og:image:alt"], [alt])


class ErrorPagesHaveNoSocialTags(ShareClient):
    def test_error_pages(self):
        for path, status in (("/no-existe/", 404), ("/en/no-existe/", 404),
                             ("/concurrencia/nope/", 404), ("/a/b/c/", 404)):
            with self.subTest(path=path):
                html = self.get(path, status)
                self.assertNotIn('rel="canonical"', html)
                self.assertNotIn('property="og:', html)
                self.assertNotIn('name="twitter:', html)
                self.assertIn('<meta name="description"', html)
        with mock.patch("app.main.logger"):  # el 405 se registra; no ensucia la salida
            html = self.client.post("/").text  # plantilla genérica
        self.assertNotIn('property="og:', html)
        self.assertNotIn('rel="canonical"', html)


class NoInsecureOrRelativeUrls(ShareClient):
    def test_social_urls_are_absolute_https(self):
        for path in ("/", "/en/", "/archivo/", "/en/archive/", "/concurrencia/",
                     "/concurrencia/concurrencia-sin-miedo/", "/en/concurrencia/fearless-concurrency/"):
            with self.subTest(path=path):
                m = metas(self.get(path))
                for key in ("canonical", "og:url", "og:image"):
                    self.assertTrue(m[key][0].startswith(BASE + "/"), (key, m[key]))
                self.assertNotIn("http://", self.get(path))


class FeedLinks(ShareClient):
    def test_head_and_footer_point_to_the_feed_of_the_page_language(self):
        for path, feed, title in (("/", "/rss.xml", "blog — Iván Vallejos · en español"),
                                  ("/en/archive/", "/en/rss.xml", "blog — Iván Vallejos · in English"),
                                  ("/en/no-existe/", "/en/rss.xml", "blog — Iván Vallejos · in English")):
            with self.subTest(path=path):
                html = self.client.get(path).text
                self.assertIn(f'<link rel="alternate" type="application/atom+xml" title="{title}" href="{feed}">', html)
                footer = html[html.index('<footer'):]
                self.assertIn(f'href="{feed}">RSS</a>', footer)

    def test_touch_icon_is_linked(self):
        self.assertIn('<link rel="apple-touch-icon" href="/static/public/apple-touch-icon.png">', self.get("/"))


class Feeds(ShareClient):
    def feed(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/atom+xml; charset=utf-8")
        self.assertEqual(response.headers["cache-control"], "public, max-age=300")
        return response.content, ET.fromstring(response.content)

    def test_each_language_has_its_own_posts_newest_first(self):
        for path, lang, slugs in (
            ("/rss.xml", "es", ["concurrencia-sin-miedo", "un-ano-escribiendo", "mudarse"]),
            ("/en/rss.xml", "en", ["fearless-concurrency", "one-design-system"]),
        ):
            with self.subTest(path=path):
                _, root = self.feed(path)
                self.assertEqual(root.get("{http://www.w3.org/XML/1998/namespace}lang"), lang)
                self.assertEqual(root.find("a:link[@rel='self']", ATOM).get("href"), BASE + path)
                links = [e.find("a:link", ATOM).get("href") for e in root.findall("a:entry", ATOM)]
                self.assertEqual([link.rstrip("/").rsplit("/", 1)[1] for link in links], slugs)
                for link in links:
                    self.assertTrue(link.startswith(BASE + ("/en/" if lang == "en" else "/")))

    def test_dates_have_an_explicit_zone(self):
        _, root = self.feed("/rss.xml")
        entry = root.find("a:entry", ATOM)
        self.assertEqual(entry.find("a:published", ATOM).text, "2026-11-14T10:00:00Z")
        self.assertTrue(root.find("a:updated", ATOM).text.endswith("Z"))

    def test_full_content_without_anchor_and_with_absolute_links(self):
        raw, root = self.feed("/rss.xml")
        entry = root.find("a:entry", ATOM)
        content = entry.find("a:content", ATOM)
        self.assertEqual(content.get("type"), "html")
        html = content.text
        post_url = f"{BASE}/concurrencia/concurrencia-sin-miedo/"
        self.assertNotIn("headerlink", html)
        self.assertIn('<h2 id="el-loop">El loop</h2>', html)
        self.assertIn(f'href="{BASE}/archivo/"', html)
        self.assertIn(f'href="{post_url}#el-loop"', html)
        self.assertIn(f'src="{BASE}/static/public/favicon.svg"', html)
        self.assertIn('href="https://docs.python.org/3/?a=1&amp;b=2"', html)
        for url in re.findall(r'(?:href|src)="([^"]*)"', html):
            self.assertTrue(url.startswith("https://"), url)
        self.assertNotIn(b"http://blog", raw)
        self.assertEqual(entry.find("a:summary", ATOM).text, "Bajada de Concurrencia sin miedo.")
        self.assertEqual(entry.find("a:category", ATOM).get("label"), "concurrencia")

    def test_english_feed_uses_english_topic_names(self):
        _, root = self.feed("/en/rss.xml")
        self.assertEqual(root.find("a:entry/a:category", ATOM).get("label"), "concurrency")
        self.assertEqual(root.find("a:title", ATOM).text, "blog — Iván Vallejos · in English")


class FeedBuilder(ShareClient):
    def test_limit_and_permanent_ids(self):
        posts = [make_post(f"Post {i}", f"post-{i}", "concurrencia", 1 + i % 28) for i in range(FEED_LIMIT + 5)]
        for post in posts:
            post.category = CATEGORIES["concurrencia"]
        posts[0].notion_id = "2a1b3c4d-0000-4000-8000-123456789abc"
        raw = build_feed(posts, "es", feed_url=f"{BASE}/rss.xml", home_url=f"{BASE}/",
                         icon_url=f"{BASE}/static/public/apple-touch-icon.png",
                         post_url=lambda p: f"{BASE}/concurrencia/{p.slug}/")
        entries = ET.fromstring(raw).findall("a:entry", ATOM)
        self.assertEqual(len(entries), FEED_LIMIT)
        # el id de Notion (UUID) no cambia aunque cambie el slug
        self.assertEqual(entries[0].find("a:id", ATOM).text, "urn:uuid:2a1b3c4d-0000-4000-8000-123456789abc")
        self.assertEqual(entries[1].find("a:id", ATOM).text, f"{BASE}/concurrencia/post-1/")

    def test_updated_is_the_notion_edit_when_later(self):
        post = make_post("Editado", "editado", "concurrencia", 14)
        post.synced_at = datetime(2026, 11, 18, 9, 30)
        raw = build_feed([post], "es", feed_url="u", home_url="h", icon_url="i", post_url=lambda p: "https://x/")
        entry = ET.fromstring(raw).find("a:entry", ATOM)
        self.assertEqual(entry.find("a:updated", ATOM).text, "2026-11-18T09:30:00Z")
        self.assertEqual(entry.find("a:published", ATOM).text, "2026-11-14T10:00:00Z")

    def test_feed_html_leaves_external_and_mail_links_alone(self):
        html = feed_html('<a href="mailto:a@b.c">m</a> <a href="//cdn.example/x">c</a>', "https://blog.example/p/")
        self.assertIn('href="mailto:a@b.c"', html)
        self.assertIn('href="https://cdn.example/x"', html)
