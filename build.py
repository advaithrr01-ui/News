#!/usr/bin/env python3
"""
Build the static site for "The Daily Twenty".

Reads one JSON file per edition from data/ and writes a deployable
static site to public/.

    python3 build.py

Edition JSON schema (data/YYYY-MM-DD.json):

{
  "date": "2026-08-11",
  "world": [
    {
      "tag": "Breaking",
      "headline": "Plain text headline",
      "body": "Two to three sentences of plain text.",
      "source_name": "CNN",
      "source_url": "https://..."
    },
    ... 10 items ...
  ],
  "india": [ ... 10 items ... ]
}

Numbering is automatic. Text is plain unicode; the builder escapes it.
"""

import html
import json
import shutil  # noqa: F401
from datetime import date as _date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
PUBLIC = ROOT / "public"

SITE_TITLE = "The Daily Twenty"
SITE_TAGLINE = "Ten stories from the world, ten from India. Every morning."

# --------------------------------------------------------------------------- #
# stylesheet
# --------------------------------------------------------------------------- #

STYLE = """
:root{
  --ink:#14110f; --ink-soft:#4a443f; --rule:#d9d2c7; --paper:#faf7f1;
  --accent:#8c2f16; --tag-bg:#efe9dd;
}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:1080px;margin:0 auto;padding:32px 28px 64px}
a{color:var(--accent)}

nav.top{display:flex;justify-content:space-between;align-items:baseline;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",sans-serif;
  font-size:11px;letter-spacing:.18em;text-transform:uppercase;
  padding-bottom:10px;margin-bottom:18px;border-bottom:1px solid var(--rule)}
nav.top a{text-decoration:none;margin-left:18px}
nav.top a:hover{text-decoration:underline}
nav.top .brand{font-weight:700;letter-spacing:.2em;color:var(--ink)}

header.masthead{border-bottom:3px double var(--ink);padding-bottom:14px;margin-bottom:6px}
.kicker{font-family:ui-sans-serif,-apple-system,"Segoe UI",sans-serif;
  font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--ink-soft)}
h1.title{font-size:52px;line-height:1;margin:8px 0 10px;letter-spacing:-.02em;font-weight:700}
h1.title a{color:inherit;text-decoration:none}
.dateline{display:flex;flex-wrap:wrap;gap:16px;justify-content:space-between;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",sans-serif;font-size:12px;
  color:var(--ink-soft);letter-spacing:.06em;text-transform:uppercase}

.cols{display:grid;grid-template-columns:1fr 1fr;gap:0 40px;margin-top:28px}
@media (max-width:820px){.cols{grid-template-columns:1fr}h1.title{font-size:36px}}
section.col{min-width:0}
h2.sec{font-family:ui-sans-serif,-apple-system,"Segoe UI",sans-serif;
  font-size:13px;letter-spacing:.2em;text-transform:uppercase;font-weight:700;
  border-bottom:2px solid var(--ink);padding-bottom:8px;margin:0 0 4px}
.col + .col{border-left:1px solid var(--rule);padding-left:40px}
@media (max-width:820px){.col + .col{border-left:0;padding-left:0;margin-top:36px}}

article{padding:18px 0;border-bottom:1px solid var(--rule)}
article:last-child{border-bottom:0}
.num{font-family:ui-sans-serif,-apple-system,sans-serif;font-size:11px;font-weight:700;
  color:var(--accent);letter-spacing:.1em}
.tag{display:inline-block;background:var(--tag-bg);color:var(--ink-soft);
  font-family:ui-sans-serif,-apple-system,sans-serif;font-size:10px;font-weight:600;
  letter-spacing:.14em;text-transform:uppercase;padding:3px 8px;border-radius:2px;margin-left:8px}
h3{font-size:20px;line-height:1.22;margin:8px 0 8px;font-weight:700;letter-spacing:-.01em}
p.body{margin:0 0 10px;font-size:15.5px;color:var(--ink-soft)}
a.src{font-family:ui-sans-serif,-apple-system,sans-serif;font-size:11.5px;
  color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(140,47,22,.35);
  letter-spacing:.04em}
a.src:hover{border-bottom-color:var(--accent)}

footer{margin-top:40px;padding-top:16px;border-top:3px double var(--ink);
  font-family:ui-sans-serif,-apple-system,sans-serif;font-size:11.5px;color:var(--ink-soft)}

aside.disclosure{display:block;margin-top:28px;padding:18px 20px;
  background:var(--tag-bg);border-left:3px solid var(--accent);
  font-family:ui-sans-serif,-apple-system,sans-serif;
  font-size:12.5px;line-height:1.6;color:var(--ink-soft)}
aside.disclosure strong{color:var(--ink)}
aside.disclosure a{color:var(--accent)}

/* archive */
ul.archive{list-style:none;padding:0;margin:24px 0 0}
ul.archive li{border-bottom:1px solid var(--rule);padding:16px 0;
  display:flex;justify-content:space-between;align-items:baseline;gap:20px}
ul.archive a{font-size:19px;font-weight:700;text-decoration:none;letter-spacing:-.01em}
ul.archive a:hover{text-decoration:underline}
ul.archive .lede{font-size:14px;color:var(--ink-soft);text-align:right;
  flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media (max-width:640px){ul.archive li{flex-direction:column;gap:4px}
  ul.archive .lede{text-align:left;white-space:normal}}
"""

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #


def e(text):
    """Escape plain text for HTML."""
    return html.escape(str(text), quote=True)


def pretty_date(iso):
    """2026-08-11 -> Tuesday, 11 August 2026"""
    y, m, d = (int(p) for p in iso.split("-"))
    dt = _date(y, m, d)
    return f"{dt:%A}, {dt.day} {dt:%B %Y}"


def short_date(iso):
    """2026-08-11 -> 11 Aug 2026"""
    y, m, d = (int(p) for p in iso.split("-"))
    dt = _date(y, m, d)
    return f"{dt.day} {dt:%b %Y}"


def page(title, body, css_path="style.css", nav_home="index.html",
         nav_archive="archive.html", description=SITE_TAGLINE):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(SITE_TITLE)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
<link rel="stylesheet" href="{css_path}">
</head>
<body>
<div class="wrap">
<nav class="top">
  <span class="brand">{e(SITE_TITLE)}</span>
  <span>
    <a href="{nav_home}">Latest</a>
    <a href="{nav_archive}">Archive</a>
  </span>
</nav>
{body}
<aside class="disclosure">
  <strong>How this is made.</strong> The Daily Twenty is compiled automatically, once
  each morning, by an AI system that searches published reporting and writes the
  summaries you see here. No journalist reports these stories and no editor reviews
  the page before it goes live.
  <br><br>
  That means errors are possible and will not be caught quickly — a misstated figure,
  a garbled detail, a story missed entirely. Every item links to the outlet that
  reported it. <strong>Follow the link before relying on anything here</strong>,
  particularly for casualty figures, legal outcomes, market data, or anything
  concerning a named individual.
  <br><br>
  Original reporting belongs to the publications credited. Spotted a mistake?
  <a href="https://github.com/advaithrr01-ui/News/issues">Report it here</a>.
</aside>
</div>
</body>
</html>
"""


def render_article(index, item):
    return f"""  <article>
    <span class="num">{index:02d}</span><span class="tag">{e(item['tag'])}</span>
    <h3>{e(item['headline'])}</h3>
    <p class="body">{e(item['body'])}</p>
    <a class="src" href="{e(item['source_url'])}" target="_blank" rel="noopener">{e(item['source_name'])} &rarr;</a>
  </article>"""


def render_column(heading, items):
    articles = "\n".join(render_article(i, it) for i, it in enumerate(items, 1))
    return f"""<section class="col">
  <h2 class="sec">{e(heading)}</h2>
{articles}
</section>"""


def render_edition(ed, css_path="style.css", nav_home="index.html",
                   nav_archive="archive.html"):
    iso = ed["date"]
    body = f"""<header class="masthead">
  <div class="kicker">Daily Global &amp; India Digest &nbsp;&middot;&nbsp; Ten + Ten</div>
  <h1 class="title"><a href="{nav_home}">{e(SITE_TITLE)}</a></h1>
  <div class="dateline">
    <span>{e(pretty_date(iso))}</span>
    <span>Tech &middot; Geopolitics &middot; Policy &amp; Economy &middot; Science &middot; Sport</span>
  </div>
</header>

<div class="cols">
{render_column("World", ed["world"])}
{render_column("India", ed["india"])}
</div>

<footer>
  Compiled {e(pretty_date(iso))} &nbsp;&middot;&nbsp; Twenty items, ten global and ten from India,
  across technology &amp; AI, geopolitics &amp; defence, government policy &amp; economy,
  science &amp; climate, and sport. Every item links to its source; follow the link
  before acting on anything time-sensitive.
</footer>"""
    leads = [c[0]["headline"] for c in (ed["world"], ed["india"]) if c]
    desc = " · ".join(leads) if leads else SITE_TAGLINE
    return page(f"{SITE_TITLE} — {short_date(iso)}", body,
                css_path=css_path, nav_home=nav_home, nav_archive=nav_archive,
                description=desc)


def render_archive(editions):
    rows = []
    for ed in editions:
        iso = ed["date"]
        lede = ed["world"][0]["headline"] if ed.get("world") else ""
        rows.append(
            f"""  <li>
    <a href="editions/{e(iso)}.html">{e(short_date(iso))}</a>
    <span class="lede">{e(lede)}</span>
  </li>"""
        )
    body = f"""<header class="masthead">
  <div class="kicker">Every edition, newest first</div>
  <h1 class="title"><a href="index.html">Archive</a></h1>
  <div class="dateline">
    <span>{len(editions)} edition{'s' if len(editions) != 1 else ''}</span>
    <span>{e(SITE_TAGLINE)}</span>
  </div>
</header>

<ul class="archive">
{chr(10).join(rows)}
</ul>"""
    return page(f"{SITE_TITLE} — Archive", body)


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #


def load_editions():
    editions = []
    for path in sorted(DATA.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            ed = json.load(fh)
        for key in ("date", "world", "india"):
            if key not in ed:
                raise ValueError(f"{path.name}: missing required key {key!r}")
        for side in ("world", "india"):
            n = len(ed[side])
            if n != 10:
                print(f"  ! warning: {path.name} has {n} {side} items (expected 10)")
        editions.append(ed)
    return editions


def main():
    editions = load_editions()
    if not editions:
        raise SystemExit("No editions found in data/. Nothing to build.")

    (PUBLIC / "editions").mkdir(parents=True, exist_ok=True)

    (PUBLIC / "style.css").write_text(STYLE.strip() + "\n", encoding="utf-8")

    # dated edition pages (one level deep -> paths need ../)
    for ed in editions:
        out = PUBLIC / "editions" / f"{ed['date']}.html"
        out.write_text(
            render_edition(ed, css_path="../style.css",
                           nav_home="../index.html",
                           nav_archive="../archive.html"),
            encoding="utf-8",
        )

    # homepage = newest edition
    newest = max(editions, key=lambda x: x["date"])
    (PUBLIC / "index.html").write_text(render_edition(newest), encoding="utf-8")

    # archive, newest first
    ordered = sorted(editions, key=lambda x: x["date"], reverse=True)
    (PUBLIC / "archive.html").write_text(render_archive(ordered), encoding="utf-8")

    print(f"Built {len(editions)} edition(s) -> {PUBLIC}")
    print(f"  homepage: {newest['date']}")


if __name__ == "__main__":
    main()
