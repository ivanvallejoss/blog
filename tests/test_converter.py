"""
Pruebas del conversor de Notion (`notion/converter.py`).

Los bloques están escritos a mano con la forma de la API de Notion (solo las
claves que el conversor lee). Cada caso mira el markdown que sale y, cuando
importa cómo se ve, el HTML que da `app/render.py`, que es lo que llega a la
página.

    uv run python -m unittest
"""
import unittest

from app.render import render_markdown
from notion.converter import CHILD_TYPES, code_language, convert_blocks, escape_text


# — fábricas de bloques —

def text(content, href=None, **annotations):
    """Fragmento de rich_text. annotations: bold, italic, strikethrough, code…"""
    return {
        "type": "text",
        "plain_text": content,
        "href": href,
        "annotations": {
            "bold": False, "italic": False, "strikethrough": False,
            "underline": False, "code": False, "color": "default",
            **annotations,
        },
    }


def block(kind, *rich_text, children=None, **data):
    result = {
        "object": "block",
        "type": kind,
        "has_children": bool(children),
        kind: {"rich_text": list(rich_text), **data},
    }
    if children:
        result["children"] = children
    return result


def para(*rich_text, **kw):
    return block("paragraph", *rich_text, **kw)


def bullet(*rich_text, **kw):
    return block("bulleted_list_item", *rich_text, **kw)


def number(*rich_text, **kw):
    return block("numbered_list_item", *rich_text, **kw)


def md(*blocks):
    return convert_blocks(list(blocks)).markdown


def html(*blocks):
    return render_markdown(md(*blocks))[0]


class BlockTypes(unittest.TestCase):
    def test_paragraph(self):
        self.assertEqual(md(para(text("Hola mundo"))), "Hola mundo\n")
        self.assertEqual(html(para(text("Hola mundo"))), "<p>Hola mundo</p>")

    def test_blocks_are_separated_by_a_blank_line(self):
        self.assertEqual(md(para(text("a")), para(text("b"))), "a\n\nb\n")

    def test_empty_paragraph_is_skipped(self):
        self.assertEqual(md(para(text("a")), para(), para(text("b"))), "a\n\nb\n")

    def test_no_blocks(self):
        self.assertEqual(md(), "")

    def test_heading_1_is_h2(self):
        # El H1 de la página es el título del post.
        self.assertEqual(md(block("heading_1", text("Uno"))), "## Uno\n")
        self.assertIn("<h2", html(block("heading_1", text("Uno"))))

    def test_heading_2_and_3(self):
        self.assertEqual(md(block("heading_2", text("Dos"))), "## Dos\n")
        self.assertEqual(md(block("heading_3", text("Tres"))), "### Tres\n")

    def test_heading_keeps_permalink_and_toc(self):
        content_html, toc = render_markdown(md(
            block("heading_2", text("El problema")),
            block("heading_3", text("Un detalle")),
        ))
        self.assertIn('<h2 id="el-problema">', content_html)
        self.assertIn('class="headerlink" href="#el-problema"', content_html)
        self.assertEqual(toc, [
            {"level": 2, "id": "el-problema", "text": "El problema"},
            {"level": 3, "id": "un-detalle", "text": "Un detalle"},
        ])

    def test_toc_text_is_plain_text(self):
        _, toc = render_markdown(md(block("heading_2", text("A & <b> "), text("c", code=True))))
        self.assertEqual(toc[0]["text"], "A & <b> c")

    def test_toggleable_heading_children_follow_it(self):
        out = md(block("heading_2", text("Título"), children=[para(text("dentro"))], is_toggleable=True))
        self.assertEqual(out, "## Título\n\ndentro\n")

    def test_quote(self):
        self.assertEqual(md(block("quote", text("Una cita"))), "> Una cita\n")
        self.assertEqual(html(block("quote", text("Una cita"))), "<blockquote>\n<p>Una cita</p>\n</blockquote>")

    def test_quote_with_children(self):
        out = md(block("quote", text("Arriba"), children=[para(text("abajo"))]))
        self.assertEqual(out, "> Arriba\n>\n> abajo\n")
        self.assertEqual(
            render_markdown(out)[0],
            "<blockquote>\n<p>Arriba</p>\n<p>abajo</p>\n</blockquote>",
        )

    def test_divider(self):
        self.assertEqual(md(para(text("a")), block("divider"), para(text("b"))), "a\n\n---\n\nb\n")
        self.assertIn("<hr />", html(para(text("a")), block("divider")))

    def test_code_block(self):
        out = md(block("code", text("print(1)"), language="python"))
        self.assertEqual(out, "```python\nprint(1)\n```\n")
        self.assertIn('<div class="codehilite"><pre>', render_markdown(out)[0])

    def test_code_block_is_not_escaped(self):
        out = md(block("code", text("a = b * c  # <x> & _y_"), language="python"))
        self.assertIn("a = b * c  # <x> & _y_", out)
        rendered = html(block("code", text("x = '<b>'"), language="plain text"))
        self.assertIn("x = &#39;&lt;b&gt;&#39;", rendered.replace("'", "&#39;"))

    def test_code_block_with_fence_inside_uses_a_longer_fence(self):
        out = md(block("code", text("```\nadentro\n```"), language="markdown"))
        self.assertTrue(out.startswith("````markdown\n"))
        self.assertTrue(out.endswith("\n````\n"))
        self.assertIn("adentro", html(block("code", text("```\nadentro\n```"), language="markdown")))

    def test_code_block_with_plain_text_stays_a_block(self):
        # Con «plain text» la cerca dejaba de ser cerca y salía como texto en línea.
        rendered = html(block("code", text("hola\nchau"), language="plain text"))
        self.assertIn('<div class="codehilite">', rendered)
        self.assertNotIn("<p>", rendered)

    def test_code_block_text_is_concatenated(self):
        out = md(block("code", text("a"), text("b", bold=True), language="text"))
        self.assertIn("\nab\n", out)


class CodeLanguages(unittest.TestCase):
    def test_known_language_passes(self):
        self.assertEqual(code_language("python"), "python")
        self.assertEqual(code_language("JavaScript"), "javascript")

    def test_notion_names_are_mapped(self):
        self.assertEqual(code_language("plain text"), "text")
        self.assertEqual(code_language("c++"), "cpp")
        self.assertEqual(code_language("c#"), "csharp")
        self.assertEqual(code_language("shell"), "bash")
        self.assertEqual(code_language("visual basic"), "vb.net")
        self.assertEqual(code_language("java/c/c++/c#"), "java")
        self.assertEqual(code_language("markup"), "html")

    def test_unknown_or_empty_falls_back_to_text(self):
        self.assertEqual(code_language("mermaid"), "text")
        self.assertEqual(code_language("idioma inventado"), "text")
        self.assertEqual(code_language(""), "text")
        self.assertEqual(code_language(None), "text")

    def test_every_notion_language_gives_a_working_fence(self):
        notion_languages = [
            "abap", "arduino", "bash", "basic", "c", "clojure", "coffeescript", "c++", "c#",
            "css", "dart", "diff", "docker", "elixir", "elm", "erlang", "flow", "fortran", "f#",
            "gherkin", "glsl", "go", "graphql", "groovy", "haskell", "html", "java",
            "javascript", "json", "julia", "kotlin", "latex", "less", "lisp", "livescript",
            "lua", "makefile", "markdown", "markup", "matlab", "mermaid", "nix", "objective-c",
            "ocaml", "pascal", "perl", "php", "plain text", "powershell", "prolog", "protobuf",
            "python", "r", "reason", "ruby", "rust", "sass", "scala", "scheme", "scss", "shell",
            "sql", "swift", "typescript", "vb.net", "verilog", "vhdl", "visual basic",
            "webassembly", "xml", "yaml", "java/c/c++/c#",
        ]
        for name in notion_languages:
            with self.subTest(language=name):
                rendered = html(block("code", text("x"), language=name))
                self.assertIn('<div class="codehilite">', rendered)
                self.assertNotIn("```", rendered)


class InlineFormatting(unittest.TestCase):
    def test_each_annotation(self):
        self.assertEqual(md(para(text("n", bold=True))), "<strong>n</strong>\n")
        self.assertEqual(md(para(text("i", italic=True))), "<em>i</em>\n")
        self.assertEqual(md(para(text("t", strikethrough=True))), "<del>t</del>\n")
        self.assertEqual(md(para(text("c", code=True))), "<code>c</code>\n")

    def test_link(self):
        self.assertEqual(
            md(para(text("sitio", href="https://ivanvallejos.dev/"))),
            '<a href="https://ivanvallejos.dev/">sitio</a>\n',
        )

    def test_link_url_is_escaped_in_the_attribute(self):
        out = md(para(text("x", href='https://e.com/?a=1&b="2"')))
        self.assertIn('href="https://e.com/?a=1&amp;b=&quot;2&quot;"', out)

    def test_combined_formatting(self):
        rendered = html(para(text("todo", href="https://e.com", bold=True, italic=True, strikethrough=True)))
        self.assertEqual(
            rendered,
            '<p><a href="https://e.com"><strong><em><del>todo</del></em></strong></a></p>',
        )

    def test_bold_code(self):
        self.assertEqual(html(para(text("x()", bold=True, code=True))), "<p><strong><code>x()</code></strong></p>")

    def test_mixed_fragments_in_one_paragraph(self):
        rendered = html(para(
            text("Con "), text("TaskGroup", code=True), text(", si una tarea "),
            text("falla", bold=True), text(", las demás se "), text("cancelan", italic=True), text("."),
        ))
        self.assertEqual(
            rendered,
            "<p>Con <code>TaskGroup</code>, si una tarea <strong>falla</strong>, "
            "las demás se <em>cancelan</em>.</p>",
        )

    def test_edge_spaces_stay_outside_the_tags(self):
        # Notion suele meter el espacio siguiente dentro de la negrita.
        self.assertEqual(md(para(text("a "), text("negrita ", bold=True), text("b"))), "a <strong>negrita</strong> b\n")

    def test_intraword_formatting(self):
        self.assertEqual(html(para(text("des"), text("hacer", italic=True))), "<p>des<em>hacer</em></p>")

    def test_adjacent_fragments_with_the_same_format_are_merged(self):
        self.assertEqual(md(para(text("ho", bold=True), text("la", bold=True))), "<strong>hola</strong>\n")

    def test_line_break_inside_a_block(self):
        self.assertEqual(html(para(text("uno\ndos"))), "<p>uno<br>dos</p>")
        self.assertEqual(html(para(text("uno\n", bold=True), text("dos"))), "<p><strong>uno</strong><br>dos</p>")

    def test_underline_and_color_are_ignored(self):
        self.assertEqual(md(para(text("x", underline=True, color="red"))), "x\n")

    def test_notion_internal_link_keeps_the_text_and_is_reported(self):
        result = convert_blocks([para(text("otra página", href="/0f2b7c1e9d8a4b3c"))])
        self.assertEqual(result.markdown, "otra página\n")
        self.assertEqual(result.unsupported["link interno de Notion"], 1)
        result = convert_blocks([para(text("x", href="https://www.notion.so/abc"))])
        self.assertEqual(result.markdown, "x\n")

    def test_unsafe_link_scheme_is_dropped(self):
        result = convert_blocks([para(text("x", href="javascript:alert(1)"))])
        self.assertEqual(result.markdown, "x\n")
        self.assertEqual(sum(result.unsupported.values()), 1)

    def test_formatting_inside_headings_lists_and_quotes(self):
        self.assertIn("<h2", html(block("heading_2", text("Con "), text("código", code=True))))
        self.assertIn("<code>código</code>", html(block("heading_2", text("Con "), text("código", code=True))))
        self.assertIn("<li><strong>a</strong></li>", html(bullet(text("a", bold=True))))
        self.assertIn("<p><em>a</em></p>", html(block("quote", text("a", italic=True))))


class Escaping(unittest.TestCase):
    def assertLiteral(self, content):
        """El texto llega a la página tal cual, sin volverse formato ni etiqueta."""
        rendered = html(para(text(content)))
        expected = (
            content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        self.assertEqual(rendered, f"<p>{expected}</p>")

    def test_markdown_characters(self):
        for content in [
            "*no es itálica*", "**ni negrita**", "_tampoco_", "__ni esto__",
            "`no es código`", "[no es](un link)", "![ni](imagen)", "a\\b",
            "{llaves}", "3.14 y 1 + 1 - 1", "fin!", "~~no tachado~~",
        ]:
            with self.subTest(content=content):
                self.assertLiteral(content)

    def test_html_characters(self):
        for content in ["<script>alert(1)</script>", "a < b > c", "AT&T", "&amp; literal", "<b>hola</b>"]:
            with self.subTest(content=content):
                self.assertLiteral(content)

    def test_block_markers_at_the_start(self):
        for content in ["# no es título", "- no es lista", "+ tampoco", "1. ni numerada",
                        "> ni cita", "---", "    no es código"]:
            with self.subTest(content=content):
                rendered = html(para(text(content)))
                self.assertTrue(rendered.startswith("<p>"), rendered)
                self.assertIn(
                    content.strip().replace(">", "&gt;"),
                    rendered,
                )

    def test_escaping_inside_formatting(self):
        self.assertEqual(html(para(text("*x*", bold=True))), "<p><strong>*x*</strong></p>")
        self.assertEqual(html(para(text("a_b <c>", code=True))), "<p><code>a_b &lt;c&gt;</code></p>")
        self.assertEqual(html(para(text("[x]", href="https://e.com"))), '<p><a href="https://e.com">[x]</a></p>')

    def test_escaping_inside_headings_lists_and_quotes(self):
        self.assertIn("C++ &lt;3", html(block("heading_2", text("C++ <3"))))
        self.assertIn("<li>*a*</li>", html(bullet(text("*a*"))))
        self.assertIn("<p>_a_</p>", html(block("quote", text("_a_"))))

    def test_escape_text(self):
        self.assertEqual(escape_text("*a* <b>"), r"\*a\* &lt;b&gt;")


class Lists(unittest.TestCase):
    def test_bulleted_list(self):
        out = md(bullet(text("uno")), bullet(text("dos")))
        self.assertEqual(out, "- uno\n- dos\n")
        self.assertEqual(render_markdown(out)[0], "<ul>\n<li>uno</li>\n<li>dos</li>\n</ul>")

    def test_numbered_list(self):
        out = md(number(text("uno")), number(text("dos")))
        self.assertEqual(out, "1. uno\n1. dos\n")
        self.assertEqual(render_markdown(out)[0], "<ol>\n<li>uno</li>\n<li>dos</li>\n</ol>")

    def test_list_between_paragraphs(self):
        rendered = html(para(text("antes")), bullet(text("a")), para(text("después")))
        self.assertEqual(rendered, "<p>antes</p>\n<ul>\n<li>a</li>\n</ul>\n<p>después</p>")

    def test_bulleted_then_numbered_are_two_lists(self):
        rendered = html(bullet(text("a")), number(text("b")))
        self.assertEqual(rendered, "<ul>\n<li>a</li>\n</ul>\n<ol>\n<li>b</li>\n</ol>")

    def test_empty_item_without_children_is_skipped(self):
        self.assertEqual(md(bullet(text("a")), bullet()), "- a\n")

    def test_nested_bullets(self):
        out = md(
            bullet(text("uno"), children=[
                bullet(text("uno a")),
                bullet(text("uno b"), children=[bullet(text("uno b i"))]),
            ]),
            bullet(text("dos")),
        )
        self.assertEqual(out, "- uno\n    - uno a\n    - uno b\n        - uno b i\n- dos\n")
        self.assertEqual(
            render_markdown(out)[0],
            "<ul>\n<li>uno<ul>\n<li>uno a</li>\n<li>uno b<ul>\n<li>uno b i</li>\n</ul>\n"
            "</li>\n</ul>\n</li>\n<li>dos</li>\n</ul>",
        )

    def test_numbered_with_nested_bullets(self):
        rendered = html(
            number(text("paso"), children=[bullet(text("detalle"))]),
            number(text("otro paso")),
        )
        self.assertEqual(
            rendered,
            "<ol>\n<li>paso<ul>\n<li>detalle</li>\n</ul>\n</li>\n<li>otro paso</li>\n</ol>",
        )

    def test_nested_lists_of_two_types_do_not_swallow_the_next_item(self):
        rendered = html(
            bullet(text("uno"), children=[bullet(text("a")), number(text("b"))]),
            bullet(text("dos")),
        )
        self.assertEqual(rendered.count("<li>"), 4)
        self.assertIn("<ol>\n<li>b</li>\n</ol>", rendered)
        self.assertNotIn("b\n- dos", rendered)
        self.assertRegex(rendered, r"<li>\s*(<p>)?dos")

    def test_item_with_paragraph_and_code_children(self):
        rendered = html(
            bullet(text("uno"), children=[
                para(text("explicación")),
                block("code", text("print(1)"), language="python"),
            ]),
            bullet(text("dos")),
        )
        self.assertEqual(rendered.count("<li>"), 2)
        self.assertIn("<p>explicación</p>", rendered)
        self.assertIn('<div class="codehilite">', rendered)
        self.assertIn('<span class="nb">print</span>', rendered)  # con colores: el lenguaje llegó
        self.assertNotIn(":::", rendered)

    def test_quote_inside_list(self):
        rendered = html(bullet(text("uno"), children=[block("quote", text("citado"))]))
        self.assertIn("<blockquote>", rendered)
        self.assertIn("citado", rendered)

    def test_list_inside_quote(self):
        rendered = html(block("quote", text("Lista:"), children=[bullet(text("a")), bullet(text("b"))]))
        self.assertIn("<blockquote>", rendered)
        self.assertIn("<ul>\n<li>a</li>\n<li>b</li>\n</ul>", rendered)

    def test_code_inside_quote(self):
        rendered = html(block("quote", text("Mirá:"), children=[block("code", text("x = 1"), language="python")]))
        self.assertIn('<div class="codehilite">', rendered)


class Unsupported(unittest.TestCase):
    def test_unsupported_blocks_are_dropped_and_counted(self):
        result = convert_blocks([
            para(text("antes")),
            {"type": "image", "image": {"type": "file", "file": {"url": "https://s3…"}}},
            {"type": "callout", "callout": {"rich_text": [text("ojo")]}},
            {"type": "image", "image": {}},
            {"type": "table", "table": {}, "has_children": True},
            para(text("después")),
        ])
        self.assertEqual(result.markdown, "antes\n\ndespués\n")
        self.assertEqual(dict(result.unsupported), {"image": 2, "callout": 1, "table": 1})

    def test_unsupported_block_inside_a_list_is_counted(self):
        result = convert_blocks([bullet(text("a"), children=[{"type": "to_do", "to_do": {}}])])
        self.assertEqual(result.markdown, "- a\n")
        self.assertEqual(result.unsupported["to_do"], 1)

    def test_unsupported_block_between_list_items_splits_the_list(self):
        rendered = html(bullet(text("a")), {"type": "image", "image": {}}, bullet(text("b")))
        self.assertEqual(rendered.count("<li>"), 2)

    def test_child_types_are_the_ones_the_converter_nests(self):
        self.assertIn("bulleted_list_item", CHILD_TYPES)
        self.assertIn("quote", CHILD_TYPES)
        self.assertNotIn("toggle", CHILD_TYPES)
        self.assertNotIn("table", CHILD_TYPES)


if __name__ == "__main__":
    unittest.main()
