# Ivan's Blog

> Personal technical blog with Notion as its content workspace.
> Posts are written and managed in Notion, then synced to a local PostgreSQL database and served via FastAPI + Jinja2.
> Notion is the source of truth — the database functions as a read cache, not a content store.

![Python](https://img.shields.io/badge/Python_3.14-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-6BA539?style=flat&logo=alembic&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Notion](https://img.shields.io/badge/Notion_API-000000?style=flat&logo=notion&logoColor=white)
![Jinja2](https://img.shields.io/badge/Jinja2-B41717?style=flat&logo=jinja&logoColor=white)
![HTMX](https://img.shields.io/badge/HTMX-3D72D7?style=flat&logo=htmx&logoColor=white)
![uv](https://img.shields.io/badge/uv-DE5FE9?style=flat&logo=uv&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)

---

## Key Decisions

These are the non-obvious design choices that shaped the system.

### Why FastAPI + SQLAlchemy instead of Django?

Django was intentionally avoided to understand what it abstracts. Using SQLAlchemy directly exposed the engine/session lifecycle, Unit of Work pattern, and migration mechanics that Django's ORM handles transparently. The friction was the point.

### Why markdown as an intermediate step?

Notion blocks are converted to Markdown (stored in `content_markdown`) rather than directly to HTML. The structure (headings, paragraphs, lists, quotes, code blocks) is plain Markdown, readable outside the rendering pipeline: if the HTML renderer changes, the content doesn't. `content_html` is a derived column, computed at sync time from `content_markdown` and never edited directly.

The stored Markdown is **not pure Markdown**, though. Inline formatting (bold, italic, strikethrough, inline code and links) is written as inline HTML (`<strong>`, `<em>`, `<del>`, `<code>`, `<a>`). Markdown's `**` and `_` markers depend on the whitespace around them, and Notion splits rich text into runs at arbitrary points (`**bold **text` is not bold), so markers would break on real content. Python-Markdown also has no strikethrough syntax. Any Markdown renderer that passes inline HTML through reads it the same way; one that strips HTML loses the formatting, not the text.

### Why share images drawn with Pillow?

Each post gets a 1200 × 630 OpenGraph image, drawn at sync time with Pillow from the same tokens and fonts as the site (`app/og/`). No headless browser and no SVG conversion on the server. The image stores a fingerprint of everything it shows: it is regenerated only when that changes, and the fingerprint becomes the `?v=` of its URL, so caches that key on the URL (Cloudflare, social networks) pick up the new one.

### Why Atom for the feed?

The feed carries full posts. Atom (RFC 4287) has an explicit `<content type="html">`, mandatory permanent ids and RFC 3339 dates. RSS 2.0 would need the `content:encoded` extension for the same thing. The URL is still `/rss.xml`: readers look at the content, not the name.

### Why notion as the primary source?

The sync layer treats Notion as the authoritative source. If a post exists in the database but not in Notion, it gets deleted. If content differs, Notion wins. The database exists to serve reads efficiently, not to own content.

## System Architecture

![How the system behaves](static/public/blog_system_pipeline.svg)

## Quick Start

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose

### Setup

#### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd blog
uv sync
```

#### 2. Configure environment variables

```bash
cp .env.example .env
```

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | yes | PostgreSQL connection string. The local database from `docker-compose.yml` listens on host port **5435**: `postgresql://blog_user:blog_password@localhost:5435/blog_db` |
| `NOTION_TOKEN` | for `sync` | Notion integration token |
| `NOTION_DATA_SOURCE_ID` | for `sync` | ID of your Notion data source |
| `BLOG_BASE_URL` | in production | Public URL without a trailing slash (`https://blog.ivanvallejos.dev`). Builds every absolute URL that leaves the site (canonical, OpenGraph, hreflang, share links, the feed) and the domain printed on share images. Without it, URLs come from the request, which behind a proxy may be `http`, and images have no domain. |
| `BLOG_LANG_SWITCH` | no | `1` shows the ES/EN switch in the header. The `/en/` routes exist either way. |
| `BLOG_SQL_ECHO` | no | `1` logs every SQL statement. |
| `BLOG_ALLOW_SEED` | dev only | `1` enables `seed-dev`. Never set it on the server. |

To get the Notion token see [Notion API getting started](https://developers.notion.com/docs/getting-started) to create an integration and get your token.

The `NOTION_DATA_SOURCE_ID` is **not** the database ID visible in the Notion URL.
It must be retrieved via the Notion API (`notion.data_sources.list()`).

The sync commands expects an inline-database element in the main page from where the Token is config + the exact properties that the "Notion Setup" section describes.

#### 3. Start the database

```bash
docker compose up -d   # PostgreSQL 16 on localhost:5435
```

#### 4. Run migrations

 ```bash
uv run alembic upgrade head
```

#### 5. Sync content from Notion

```bash
uv run python cli.py sync
```

Or, without Notion, load the sample posts of the design (both languages) with their share images:

```bash
BLOG_ALLOW_SEED=1 uv run python cli.py seed-dev
```

#### 6. Start the development server

```bash
uv run fastapi dev app/main.py
```

#### 7. Run the tests

```bash
uv run python -m unittest
```

The tests need no database and no Notion: selectors and the Notion client are replaced with in-memory fakes, and share images are drawn into a temporary folder.

### CLI Commands

All commands run as `uv run python cli.py <command>`.

| Command | Description |
| --- | --- |
| `sync [--force]` | Sync posts from Notion (creates, updates, deletes). A post is reconverted only if it changed in Notion; `--force` reconverts all of them. Also refreshes share images and deletes those of deleted posts. Reports unsupported block types, unknown `Idioma` values, topics whose slug clashes with a fixed route, and images that failed. |
| `og-images [--force]` | Generate share images in `static/og/`: the default one per language and one per post, only those missing or whose content changed (`--force`: all). Deletes images of posts that no longer exist. Exits with code 1 if any failed. |
| `touch-icon` | Redraw `static/public/apple-touch-icon.png` (committed; only needed if the ring changes). |
| `seed-dev [--clear]` | Load (or with `--clear`, remove) the design's sample posts, with their images. Needs `BLOG_ALLOW_SEED=1` and a local `DATABASE_URL`. `sync` deletes these posts: run it again after a sync. |
| `feature <slug> [--off]` | Mark (or unmark) a post as featured on the home page. |
| `backfill-db` | Recompute `content_html` from `content_markdown`. |

### Routes

| Route | Spanish | English |
| --- | --- | --- |
| Home | `/` | `/en/` |
| Archive | `/archivo/` | `/en/archive/` |
| Topic | `/{topic}/` | `/en/{topic}/` |
| Post | `/{topic}/{slug}/` | `/en/{topic}/{slug}/` |
| Feed (Atom, last 20 posts, full content) | `/rss.xml` | `/en/rss.xml` |
| Search index | `/search.json?lang=es` | `/search.json?lang=en` |

Share images are served from `/static/og/{slug}.png` and `/static/og/default/{lang}.png`. They are generated, not committed.

### Notion setup

The sync layer expects a Notion database with the following properties:

| Property | Type | Notes |
| --- | --- | --- |
| `Titulo` | Title | Required. Post title (100 characters at most) |
| `slug` | Rich text | Required. URL-friendly identifier, unique across both languages: a translation is another page with its own slug |
| `Estado` | Status | Only `Published` posts are synced |
| `categoria` | Select | Required. Avoid names whose slug is `en`, `archivo`, `archive`, `search.json`, `rss.xml` or `static` |
| `Fecha Publicacion` | Date | Required |
| `Idioma` | Select | `es` or `en` (case-insensitive). Empty means `es`; any other value falls back to `es` and is reported |
| `Resumen` | Text | Hand-written excerpt, used on the home page, in search, in the feed and as the share description. Empty: derived from the first paragraph |

**Required properties:** `Titulo`, `slug`, `Fecha Publicacion` and `categoria`. A published post with one of them empty (or an unreadable date), or with the same slug as another published post, is skipped: the other posts sync normally, and the sync summary lists it with what to fix. If it was already on the site, it is removed until it is fixed. If the Notion database lacks one of these properties altogether, the sync stops without changing anything and says which one.

Topic names are written in Spanish in Notion; their English names live in `TOPIC_NAMES` in `app/i18n.py`.

---
