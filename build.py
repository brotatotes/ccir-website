#!/usr/bin/env python3
"""
Build the Christian Church In Raleigh static site.

What it does (deliberately tiny + dependency-free — stdlib only):
  1. Reads shared partials from src/partials/ (header.html, footer.html).
  2. Reads each page in src/pages/ and injects the partials.
  3. Highlights the correct nav link using each page's `<!-- ACTIVE: key -->` marker.
  4. Writes finished, self-contained HTML into site/ at clean-URL paths.

It does NOT touch anything under site/assets/ (CSS, JS, fonts, images) or the
root files (CNAME, robots.txt, etc.) — those are edited directly and shipped as-is.

Run it with:  python3 build.py
No Node, no npm, no internet, no AI required.
"""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
PAGES = os.path.join(SRC, "pages")
PARTIALS = os.path.join(SRC, "partials")
OUT = os.path.join(ROOT, "site")

# page filename -> output path (clean URLs)
ROUTES = {
    "index.html": "index.html",
    "statement-of-faith.html": "statement-of-faith/index.html",
    "messages.html": "messages/index.html",
    "visit.html": "contact/index.html",
    "404.html": "404.html",
}

ACTIVE_ATTR = ' aria-current="page"'

# Legacy Wix URLs -> new canonical paths. Rendered as static redirect pages
# (meta refresh + canonical + JS) so old links and bookmarks keep working on
# GitHub Pages, which has no server-side redirect layer.
#   /messages is already the canonical path for Sunday Messages (no redirect needed).
REDIRECTS = {
    "about-2/index.html": "/statement-of-faith/",   # old Statement of Faith
    "about-3/index.html": "/statement-of-faith/",   # legacy about page
    "visit/index.html": "/contact/",                # first static preview path
    "visit-us/index.html": "/contact/",             # old Wix template path
}

REDIRECT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Redirecting…</title>
  <link rel="canonical" href="{target}">
  <meta name="robots" content="noindex">
  <meta http-equiv="refresh" content="0; url={target}">
  <script>location.replace({target_json});</script>
</head>
<body>
  <p>This page has moved. If you are not redirected automatically,
     <a href="{target}">continue to the new page</a>.</p>
</body>
</html>
"""


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def apply_active(html, active_key):
    """Replace {{ACTIVE:key}} tokens: matching key -> aria-current, others removed."""
    def repl(m):
        return ACTIVE_ATTR if m.group(1) == active_key else ""
    return re.sub(r"\{\{ACTIVE:([a-z0-9_-]+)\}\}", repl, html)


def build():
    header = read(os.path.join(PARTIALS, "header.html"))
    footer = read(os.path.join(PARTIALS, "footer.html"))

    built = []
    for src_name, out_rel in ROUTES.items():
        src_path = os.path.join(PAGES, src_name)
        if not os.path.exists(src_path):
            print(f"  ! skip (missing): {src_name}", file=sys.stderr)
            continue
        html = read(src_path)

        m = re.search(r"<!--\s*ACTIVE:\s*([a-z0-9_-]+)\s*-->", html)
        active_key = m.group(1) if m else ""

        html = html.replace("{{HEADER}}", header).replace("{{FOOTER}}", footer)
        html = apply_active(html, active_key)

        out_path = os.path.join(OUT, out_rel)
        write(out_path, html)
        built.append(out_rel)
        print(f"  built  {src_name:28s} -> site/{out_rel}")

    # generate legacy redirect pages
    import json
    for out_rel, target in REDIRECTS.items():
        html = REDIRECT_TEMPLATE.format(target=target, target_json=json.dumps(target))
        write(os.path.join(OUT, out_rel), html)
        print(f"  redirect {out_rel:26s} -> {target}")

    # sanity: no unresolved template tokens left in output
    leftover = []
    for out_rel in built:
        txt = read(os.path.join(OUT, out_rel))
        for tok in re.findall(r"\{\{[A-Z]", txt):
            leftover.append((out_rel, tok))
        if "{{ACTIVE:" in txt or "{{HEADER}}" in txt or "{{FOOTER}}" in txt:
            leftover.append((out_rel, "template-token"))
    if leftover:
        print("BUILD ERROR: unresolved template tokens:", leftover, file=sys.stderr)
        return 1

    print(f"\nDone. {len(built)} pages written to site/")
    return 0


if __name__ == "__main__":
    sys.exit(build())
