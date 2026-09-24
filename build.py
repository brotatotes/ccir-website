#!/usr/bin/env python3
"""
Build the Christian Church In Raleigh static site from editable content.

  content/*.json         <- words, photos, videos (edited in Pages CMS)
  content/pages/*.json   <- extra pages anyone can add in Pages CMS
  src/templates/         <- page designs (header, layout, styling hooks)
  src/partials/          <- shared header, footer, contact form
  static/                <- CSS, JS, fonts, images, favicon (copied as-is)
  site/                  <- finished website (generated, never hand-edited)

Run:  python3 build.py
Optional: BASE_PATH=/ccir-cms-test python3 build.py   (serve under a sub-path)
          NOINDEX=1                                    (hide from search engines)

Python standard library only. No Node, no npm, no AI required.
"""
import glob
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
TEMPLATES = os.path.join(ROOT, "src", "templates")
PARTIALS = os.path.join(ROOT, "src", "partials")
STATIC = os.path.join(ROOT, "static")
OUT = os.path.join(ROOT, "site")

BASE_PATH = os.environ.get("BASE_PATH", "").rstrip("/")
NOINDEX = os.environ.get("NOINDEX") == "1"
CANONICAL_HOST = os.environ.get("CANONICAL_HOST", "https://ccir.brotatotes.com")
CNAME = os.environ.get("CNAME", "")

# Built-in page slugs. Custom pages may not reuse these.
RESERVED = {"", "statement-of-faith", "messages", "contact", "assets", "about-2",
            "about-3", "visit", "visit-us", "404"}

REDIRECTS = {
    "about-2/index.html": "/statement-of-faith/",
    "about-3/index.html": "/statement-of-faith/",
    "visit/index.html": "/contact/",
    "visit-us/index.html": "/contact/",
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

ICONS = {
    "bible": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 5a2 2 0 012-2h6v16H6a2 2 0 00-2 2V5z"/><path d="M20 5a2 2 0 00-2-2h-6v16h6a2 2 0 012 2V5z"/></svg>',
    "house": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 21h18"/><path d="M5 21V9l7-5 7 5v12"/><path d="M9 21v-6h6v6"/></svg>',
    "prayer": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3v3"/><path d="M12 21a6 6 0 006-6c0-3-2.5-5-6-9-3.5 4-6 6-6 9a6 6 0 006 6z"/></svg>',
    "people": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0112 0"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.2A5 5 0 0121 19"/></svg>',
    "calendar": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
}

NUMBER_WORDS = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen"]

errors = []


# ---------------------------------------------------------------- helpers
def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load(name):
    path = os.path.join(CONTENT, name)
    try:
        return json.loads(read(path))
    except Exception as e:  # show a plain message instead of a stack trace
        errors.append(f"Could not read {name}: {e}")
        return {}


def esc(value):
    """Escape plain text for HTML."""
    return html.escape(str(value or ""), quote=True)


def rich(value):
    """Rich-text fields are saved as HTML by the editor. Plain text is wrapped."""
    value = (value or "").strip()
    if not value:
        return ""
    if not value.startswith("<"):
        return "\n".join(f"<p>{esc(p)}</p>" for p in re.split(r"\n\s*\n", value) if p.strip())
    return value


def inline(value):
    """Short text that may contain a link or bold (e.g. footer notes)."""
    value = (value or "").strip()
    if value.startswith("<p>") and value.endswith("</p>") and value.count("<p>") == 1:
        value = value[3:-4]
    return value


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return s or "page"


def youtube_id(value):
    value = (value or "").strip()
    for pat in (r"(?:v=|youtu\.be/|embed/|shorts/|live/)([A-Za-z0-9_-]{11})", r"^([A-Za-z0-9_-]{11})$"):
        m = re.search(pat, value)
        if m:
            return m.group(1)
    return ""


def picture(src, alt, width=None, height=None, lazy=True, extra=""):
    """<picture> with a WebP twin when one exists next to the JPEG/PNG."""
    if not src:
        return ""
    src = src.strip()
    webp = ""
    if src.startswith("/") and not src.lower().endswith(".webp"):
        cand = os.path.splitext(src)[0] + ".webp"
        if os.path.exists(os.path.join(STATIC, cand.lstrip("/"))):
            webp = f'<source type="image/webp" srcset="{esc(cand)}">'
    dims = f' width="{width}" height="{height}"' if width and height else ""
    load_attr = ' loading="lazy"' if lazy else ""
    return (f'<picture>{webp}<img src="{esc(src)}"{load_attr}{dims} '
            f'alt="{esc(alt)}"{extra}></picture>')


def schedule_list(times):
    rows = "".join(
        f'<li><span class="day">{esc(t.get("day"))}</span><span class="time">{esc(t.get("time"))}</span></li>'
        for t in (times or []))
    return f'<ul class="schedule">{rows}</ul>'


def cta_band(heading, text, buttons):
    if not heading and not text:
        return ""
    btns = "".join(
        f'<a class="btn {cls}" href="{esc(url)}">{esc(label)}</a>'
        for label, url, cls in buttons if label and url)
    return f"""
    <section class="section section--navy cta-band">
      <div class="wrap">
        <h2>{esc(heading)}</h2>
        <p>{esc(text)}</p>
        <div class="cta-actions">{btns}</div>
      </div>
    </section>"""


def page_banner(eyebrow, title, intro, extra=""):
    return f"""
    <section class="section section--navy" style="padding-block:clamp(3rem,7vw,5rem);">
      <div class="wrap">
        <p class="eyebrow">{esc(eyebrow)}</p>
        <h1 id="page-title" class="section-title" style="color:#fff;max-width:24ch;">{esc(title)}</h1>
        <p class="lede" style="max-width:46rem;">{esc(intro)}</p>{extra}
      </div>
    </section>"""


# ---------------------------------------------------------------- home
def render_home(h, site):
    hero = h.get("hero", {})
    who = h.get("who", {})
    bel = h.get("believe", {})
    gat = h.get("gatherings", {})
    life = h.get("life", {})
    gal = h.get("gallery", {})
    cta = h.get("cta", {})

    hero_img = hero.get("image") or "/assets/img/hero-fellowship-1280.jpg"
    stem = os.path.splitext(hero_img)[0]
    if stem == "/assets/img/hero-fellowship-1280":
        hero_pic = """<picture>
          <source type="image/webp"
            srcset="/assets/img/hero-fellowship-800.webp 800w, /assets/img/hero-fellowship-1280.webp 1280w, /assets/img/hero-fellowship-1920.webp 1920w"
            sizes="100vw">
          <img src="/assets/img/hero-fellowship-1280.jpg"
            srcset="/assets/img/hero-fellowship-800.jpg 800w, /assets/img/hero-fellowship-1280.jpg 1280w, /assets/img/hero-fellowship-1920.jpg 1920w"
            sizes="100vw" width="1920" height="1024"
            alt="%s" fetchpriority="high">
        </picture>""" % esc(hero.get("image_alt"))
    else:
        hero_pic = picture(hero_img, hero.get("image_alt"), lazy=False, extra=' fetchpriority="high"')

    cards = ""
    for c in gat.get("cards", []):
        icon = ICONS.get(c.get("icon") or "", "")
        icon_html = f'<div class="card-icon" aria-hidden="true">{icon}</div>' if icon else ""
        note = f'<p style="margin:.9rem 0 0;color:var(--muted);font-size:.95rem;">{esc(c.get("note"))}</p>' if c.get("note") else ""
        cards += f"""
          <article class="card">
            {icon_html}
            <h3>{esc(c.get("title"))}</h3>
            {schedule_list(c.get("times"))}
            {note}
          </article>"""

    cols = "".join(f"""
          <div class="prose">
            <h3>{esc(c.get("heading"))}</h3>
            <p>{esc(c.get("text"))}</p>
          </div>""" for c in life.get("columns", []))

    photos = "".join(f"<figure>{picture(p.get('image'), p.get('alt'), 600, 450)}</figure>"
                     for p in gal.get("photos", []))

    footer_note = (f'<p class="text-center mt-2" style="color:var(--muted);">{inline(gat.get("footer_note"))}</p>'
                   if gat.get("footer_note") else "")

    return f"""
    <!-- HERO -->
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero-media">
        {hero_pic}
      </div>
      <div class="wrap hero-inner">
        <h1 id="hero-title">{esc(hero.get("heading_intro"))} <span class="accent">{esc(hero.get("heading_highlight"))}</span></h1>
        <p>{esc(hero.get("text"))}</p>
        <div class="hero-actions">
          <a class="btn btn--accent" href="/contact/">Contact us</a>
          <a class="btn btn--ghost" href="/messages/">Watch a message</a>
        </div>
        <div class="hero-meta">
          <span aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
            {esc(hero.get("service_time"))}
          </span>
          <span aria-hidden="true">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-5.2-7-11a7 7 0 0114 0c0 5.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>
            {esc(hero.get("location"))}
          </span>
        </div>
      </div>
    </section>

    <!-- WHO WE ARE -->
    <section class="section section--tint" aria-labelledby="who-title">
      <div class="wrap">
        <div class="section-head center">
          <p class="eyebrow">{esc(who.get("eyebrow"))}</p>
          <h2 id="who-title" class="section-title">{esc(who.get("heading"))}</h2>
        </div>
        <p class="lead-quote text-center" style="margin-inline:auto;">{esc(who.get("text"))}</p>
      </div>
    </section>

    <!-- WHAT WE BELIEVE -->
    <section class="section" aria-labelledby="believe-title">
      <div class="wrap split">
        <div class="split-media">
          {picture(bel.get("image"), bel.get("image_alt"), 1000, 750)}
        </div>
        <div>
          <p class="eyebrow">{esc(bel.get("eyebrow"))}</p>
          <h2 id="believe-title" class="section-title">{esc(bel.get("heading"))}</h2>
          <div class="prose stack mt-2">
            {rich(bel.get("body"))}
          </div>
        </div>
      </div>
    </section>

    <!-- WEEKLY GATHERINGS -->
    <section class="section section--tint" aria-labelledby="gather-title">
      <div class="wrap">
        <div class="section-head center">
          <p class="eyebrow">{esc(gat.get("eyebrow"))}</p>
          <h2 id="gather-title" class="section-title">{esc(gat.get("heading"))}</h2>
        </div>
        <div class="grid cols-3">{cards}
        </div>
        {footer_note}
      </div>
    </section>

    <!-- CHURCH LIFE -->
    <section class="section" aria-labelledby="life-title">
      <div class="wrap">
        <div class="section-head">
          <p class="eyebrow">{esc(life.get("eyebrow"))}</p>
          <h2 id="life-title" class="section-title">{esc(life.get("heading"))}</h2>
        </div>
        <div class="grid cols-3" style="align-items:start;">{cols}
        </div>
        <div class="prose mt-2" style="max-width:52rem;">
          {rich(life.get("body"))}
        </div>
      </div>
    </section>

    <!-- GALLERY -->
    <section class="section section--tint" aria-labelledby="gallery-title">
      <div class="wrap">
        <div class="section-head center">
          <p class="eyebrow">{esc(gal.get("eyebrow"))}</p>
          <h2 id="gallery-title" class="section-title">{esc(gal.get("heading"))}</h2>
        </div>
        <div class="gallery">{photos}</div>
      </div>
    </section>
""" + cta_band(cta.get("heading"), cta.get("text"),
               [("Contact us", "/contact/", "btn--accent"),
                ("Email us", "mailto:" + site.get("email", ""), "btn--ghost")])


# ---------------------------------------------------------------- statement of faith
def render_faith(f):
    items = []
    for i, p in enumerate(f.get("points", [])):
        label = NUMBER_WORDS[i] if i < len(NUMBER_WORDS) else str(i + 1)
        items.append(f"""
          <article class="stack">
            <p class="eyebrow" style="color:var(--accent);">{label}</p>
            <h2 style="font-size:1.4rem;margin:.1rem 0 .5rem;">{esc(p.get("heading"))}</h2>
            <p>{esc(p.get("text"))}</p>
          </article>""")
    sep = '\n\n          <hr style="border:none;border-top:1px solid var(--line);margin:2.5rem 0;">\n'
    return page_banner(f.get("eyebrow"), f.get("title"), f.get("intro")) + f"""

    <section class="section">
      <div class="wrap">
        <div class="prose" style="max-width:48rem;">
{sep.join(items)}
        </div>
      </div>
    </section>
""" + cta_band(f.get("cta_heading"), f.get("cta_text"),
               [("Contact us", "/contact/", "btn--accent"),
                ("Watch Sunday messages", "/messages/", "btn--ghost")])


# ---------------------------------------------------------------- messages
def video_card(title, vid):
    t = esc(title)
    local = os.path.join(STATIC, "assets", "img", "thumbs", vid + ".jpg")
    if os.path.exists(local):
        thumb = (f'<source type="image/webp" srcset="/assets/img/thumbs/{vid}.webp">'
                 f'<img src="/assets/img/thumbs/{vid}.jpg" loading="lazy" width="640" height="360" alt="Thumbnail for {t}">')
    else:
        thumb = (f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" loading="lazy" '
                 f'width="640" height="360" alt="Thumbnail for {t}">')
    return f"""
          <article class="video-card">
            <div class="video-embed" role="button" tabindex="0" data-yt="{vid}" data-title="{t}" aria-label="Play video: {t}">
              <picture>{thumb}</picture>
              <span class="play" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></span>
            </div>
            <div class="meta">
              <h3>{t}</h3>
              <a href="https://www.youtube.com/watch?v={vid}" rel="noopener">Watch on YouTube &#8594;</a>
            </div>
          </article>"""


def render_messages(m):
    cards = ""
    for v in m.get("videos", []):
        vid = youtube_id(v.get("youtube"))
        if not vid:
            errors.append(f"Sunday Messages: could not find a YouTube video in {v.get('youtube')!r} ({v.get('title')!r})")
            continue
        cards += video_card(v.get("title"), vid)
    channel = esc(m.get("youtube_channel"))
    handle = re.search(r"/(@[A-Za-z0-9_.-]+)", m.get("youtube_channel") or "")
    channel_label = f"YouTube {handle.group(1)}" if handle else "our YouTube channel"
    button = f"""
        <div class="cta-actions" style="justify-content:flex-start;margin-top:1.4rem;">
          <a class="btn btn--accent" href="{channel}" rel="noopener">Visit our YouTube channel</a>
        </div>"""
    return page_banner(m.get("eyebrow"), m.get("title"), m.get("intro"), button) + f"""

    <section class="section">
      <div class="wrap">
        <div class="video-grid">{cards}
        </div>
        <p class="text-center mt-2" style="color:var(--muted);">
          Looking for more? All of our messages live on
          <a href="{channel}" rel="noopener">{esc(channel_label)}</a>.
        </p>
      </div>
    </section>
""" + cta_band(m.get("cta_heading"), m.get("cta_text"), [("Contact us", "/contact/", "btn--accent")])


# ---------------------------------------------------------------- contact
def render_contact(c, site):
    cards = ""
    for s in c.get("schedule", []):
        note = f'<p style="margin:.9rem 0 0;color:var(--muted);font-size:.95rem;">{esc(s.get("note"))}</p>' if s.get("note") else ""
        cards += f"""
          <article class="card">
            <h3>{esc(s.get("title"))}</h3>
            {schedule_list(s.get("times"))}
            {note}
          </article>"""
    email = esc(c.get("email") or site.get("email"))
    form = read(os.path.join(PARTIALS, "contact-form.html"))
    return page_banner(c.get("eyebrow"), c.get("title"), c.get("intro")) + f"""

    <!-- SCHEDULE -->
    <section class="section section--tint">
      <div class="wrap">
        <div class="section-head">
          <p class="eyebrow">{esc(c.get("schedule_eyebrow"))}</p>
          <h2 class="section-title">{esc(c.get("schedule_heading"))}</h2>
        </div>
        <div class="grid cols-3">{cards}
        </div>
      </div>
    </section>

    <!-- CONTACT + FORM -->
    <section class="section">
      <div class="wrap">
        <div class="contact-grid">
          <div>
            <div class="section-head">
              <p class="eyebrow">Get in touch</p>
              <h2 class="section-title">Reach out any time</h2>
            </div>
            <ul class="info-list">
              <li>
                <span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg></span>
                <span><span class="label">Email</span><a href="mailto:{email}">{email}</a></span>
              </li>
              <li>
                <span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-5.2-7-11a7 7 0 0114 0c0 5.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg></span>
                <span><span class="label">Where we meet</span>{esc(c.get("meeting_place"))}<br><span style="color:var(--muted);font-size:.92rem;">{esc(c.get("meeting_note"))}</span></span>
              </li>
              <li>
                <span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></span>
                <span><span class="label">Sunday service</span>{esc(c.get("sunday_service"))}</span>
              </li>
              <li>
                <span class="ico" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 12s0-3.2-.4-4.7a2.5 2.5 0 00-1.8-1.8C19.3 5 12 5 12 5s-7.3 0-8.8.5A2.5 2.5 0 001.4 7.3C1 8.8 1 12 1 12s0 3.2.4 4.7a2.5 2.5 0 001.8 1.8C4.7 19 12 19 12 19s7.3 0 8.8-.5a2.5 2.5 0 001.8-1.8C23 15.2 23 12 23 12z"/></svg></span>
                <span><span class="label">Follow along</span><a href="{esc(site.get('youtube'))}" rel="noopener">YouTube</a> · <a href="{esc(site.get('instagram'))}" rel="noopener">Instagram</a> · <a href="{esc(site.get('facebook'))}" rel="noopener">Facebook</a></span>
              </li>
            </ul>
          </div>

{form}
        </div>
      </div>
    </section>
""" + cta_band(c.get("cta_heading"), c.get("cta_text"),
               [("Email us", "mailto:" + (c.get("email") or site.get("email", "")), "btn--accent")])


# ---------------------------------------------------------------- custom pages (blocks)
def render_block(b):
    kind = b.get("type")
    if kind == "text":
        heading = (f'<h2 class="section-title" style="margin-bottom:1.25rem;">{esc(b.get("heading"))}</h2>'
                   if b.get("heading") else "")
        return f"""
    <section class="section{' section--tint' if b.get('shaded') else ''}">
      <div class="wrap">
        <div class="prose" style="max-width:48rem;">
          {heading}
          {rich(b.get("body"))}
        </div>
      </div>
    </section>"""
    if kind == "image_text":
        img = f'<div class="split-media">{picture(b.get("image"), b.get("image_alt"))}</div>'
        words = f"""<div>
          {f'<h2 class="section-title">{esc(b.get("heading"))}</h2>' if b.get("heading") else ""}
          <div class="prose stack mt-2">{rich(b.get("body"))}</div>
        </div>"""
        inner = words + img if b.get("image_side") == "right" else img + words
        return f"""
    <section class="section{' section--tint' if b.get('shaded') else ''}">
      <div class="wrap split">
        {inner}
      </div>
    </section>"""
    if kind == "columns":
        cols = b.get("columns") or []
        n = 2 if len(cols) == 2 else 3
        items = "".join(f"""
          <div class="prose">
            <h3>{esc(c.get("heading"))}</h3>
            {rich(c.get("text"))}
          </div>""" for c in cols)
        heading = (f'<div class="section-head"><h2 class="section-title">{esc(b.get("heading"))}</h2></div>'
                   if b.get("heading") else "")
        return f"""
    <section class="section{' section--tint' if b.get('shaded') else ''}">
      <div class="wrap">
        {heading}
        <div class="grid cols-{n}" style="align-items:start;">{items}
        </div>
      </div>
    </section>"""
    if kind == "video":
        vid = youtube_id(b.get("youtube"))
        if not vid:
            errors.append(f"Video section: could not find a YouTube video in {b.get('youtube')!r}")
            return ""
        return f"""
    <section class="section{' section--tint' if b.get('shaded') else ''}">
      <div class="wrap" style="max-width:48rem;">
        <div class="video-grid" style="grid-template-columns:1fr;">{video_card(b.get("title") or "Video", vid)}
        </div>
      </div>
    </section>"""
    if kind == "cta":
        return cta_band(b.get("heading"), b.get("text"),
                        [(b.get("button_label"), b.get("button_link"), "btn--accent")])
    errors.append(f"Unknown section type: {kind!r}")
    return ""


def load_custom_pages():
    pages = []
    for path in sorted(glob.glob(os.path.join(CONTENT, "pages", "*.json"))):
        data = load(os.path.join("pages", os.path.basename(path)))
        if not data:
            continue
        slug = slugify(os.path.splitext(os.path.basename(path))[0])
        if slug in RESERVED:
            errors.append(f"Page {data.get('title')!r} uses a reserved address /{slug}/. Rename it.")
            continue
        if data.get("published") is False:
            continue
        data["_slug"] = slug
        pages.append(data)
    pages.sort(key=lambda p: (p.get("menu_order") or 99, p.get("title") or ""))
    return pages


def render_custom(p):
    body = page_banner(p.get("eyebrow"), p.get("title"), p.get("intro"))
    return body + "".join(render_block(b) for b in (p.get("sections") or []))


# ---------------------------------------------------------------- assembly
def build_header(custom):
    items = ['<li><a href="/"{{ACTIVE:home}}>Home</a></li>',
             '<li><a href="/statement-of-faith/"{{ACTIVE:faith}}>Statement of Faith</a></li>',
             '<li><a href="/messages/"{{ACTIVE:messages}}>Sunday Messages</a></li>']
    for p in custom:
        if p.get("show_in_menu"):
            label = p.get("menu_label") or p.get("title")
            items.append(f'<li><a href="/{p["_slug"]}/"{{{{ACTIVE:page-{p["_slug"]}}}}}>{esc(label)}</a></li>')
    items.append('<li class="nav-cta"><a href="/contact/"{{ACTIVE:visit}}>Contact</a></li>')
    header = read(os.path.join(PARTIALS, "header.html"))
    return re.sub(r'(<ul class="nav-menu" id="nav-menu">).*?(</ul>)',
                  lambda m: m.group(1) + "\n          " + "\n          ".join(items) + "\n        " + m.group(2),
                  header, flags=re.S)


def build_footer(site, custom):
    footer = read(os.path.join(PARTIALS, "footer.html"))
    extra = "".join(f'\n            <li><a href="/{p["_slug"]}/">{esc(p.get("menu_label") or p.get("title"))}</a></li>'
                    for p in custom if p.get("show_in_menu"))
    if extra:
        footer = footer.replace('<li><a href="/contact/">Contact</a></li>',
                                extra.lstrip("\n") + '\n            <li><a href="/contact/">Contact</a></li>')
    footer = re.sub(r'(<div class="footer-brand">\s*<span class="brand-name">).*?(</span>\s*<p>).*?(</p>)',
                    lambda m: m.group(1) + esc(site.get("church_name")) + m.group(2) + esc(site.get("footer_blurb")) + m.group(3),
                    footer, flags=re.S)
    connect = (f'<li><a href="mailto:{esc(site.get("email"))}">{esc(site.get("email"))}</a></li>\n'
               f'            <li>Meeting place: {esc(site.get("meeting_place"))}</li>\n'
               f'            <li>{esc(site.get("service_time"))}</li>')
    footer = re.sub(r'(<h4>Connect</h4>\s*<ul class="footer-links">).*?(</ul>)',
                    lambda m: m.group(1) + "\n            " + connect + "\n          " + m.group(2),
                    footer, flags=re.S)
    for key, label in (("youtube", "YouTube channel"), ("instagram", "Instagram"), ("facebook", "Facebook")):
        if site.get(key):
            footer = re.sub(r'<a href="[^"]*" aria-label="%s"' % label,
                            f'<a href="{esc(site[key])}" aria-label="{label}"', footer)
    footer = re.sub(r'(Christian Church In Raleigh\. ).*?(</span>)',
                    lambda m: m.group(1) + esc(site.get("footer_tagline")) + m.group(2), footer, count=1)
    return footer


def apply_active(text, key):
    return re.sub(r"\{\{ACTIVE:([a-z0-9_-]+)\}\}",
                  lambda m: ' aria-current="page"' if m.group(1) == key else "", text)


def finalize(text):
    if NOINDEX:
        text = text.replace("<head>", '<head>\n  <meta name="robots" content="noindex, nofollow">', 1)
    if BASE_PATH:
        # Prefix root-relative links so the site works under a sub-path.
        text = re.sub(r'((?:href|src|action)=")/(?!/)', r"\1" + BASE_PATH + "/", text)
        text = re.sub(r'(srcset=")([^"]*)"',
                      lambda m: m.group(1) + re.sub(r'(^|,\s*)/(?!/)', r"\1" + BASE_PATH + "/", m.group(2)) + '"',
                      text)
        text = text.replace("location.replace(\"/", "location.replace(\"" + BASE_PATH + "/")
        text = re.sub(r'(content="0; url=)/', r"\1" + BASE_PATH + "/", text)
    text = text.replace("https://ccir.brotatotes.com", CANONICAL_HOST)
    return text


def render(template, main, key, header, footer, tokens=None):
    html_text = read(os.path.join(TEMPLATES, template))
    for k, v in (tokens or {}).items():
        html_text = html_text.replace("{{" + k + "}}", v)
    html_text = html_text.replace("{{HEADER}}", header).replace("{{FOOTER}}", footer)
    html_text = html_text.replace("{{MAIN}}", main)
    html_text = re.sub(r"<!--\s*ACTIVE:\s*[a-z0-9{}_-]+\s*-->", f"<!-- ACTIVE: {key} -->", html_text)
    return finalize(apply_active(html_text, key))


def build():
    site = load("site.json")
    home = load("home.json")
    faith = load("statement-of-faith.json")
    msgs = load("messages.json")
    contact = load("contact.json")
    custom = load_custom_pages()
    if errors:
        return report()

    header = build_header(custom)
    footer = build_footer(site, custom)

    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    if CNAME:
        write(os.path.join(OUT, "CNAME"), CNAME + "\n")

    outputs = [
        ("home.html", render_home(home, site), "home", "index.html"),
        ("statement-of-faith.html", render_faith(faith), "faith", "statement-of-faith/index.html"),
        ("messages.html", render_messages(msgs), "messages", "messages/index.html"),
        ("contact.html", render_contact(contact, site), "visit", "contact/index.html"),
    ]
    built = []
    for template, main, key, out_rel in outputs:
        write(os.path.join(OUT, out_rel), render(template, main, key, header, footer))
        built.append(out_rel)
        print(f"  built  {out_rel}")

    for p in custom:
        slug = p["_slug"]
        desc = p.get("description") or p.get("intro") or p.get("title") or ""
        tokens = {"PAGE_TITLE": esc(p.get("title")), "PAGE_DESCRIPTION": esc(desc),
                  "PAGE_SLUG": slug, "ACTIVE_KEY": f"page-{slug}"}
        out_rel = f"{slug}/index.html"
        write(os.path.join(OUT, out_rel),
              render("page.html", render_custom(p), f"page-{slug}", header, footer, tokens))
        built.append(out_rel)
        print(f"  built  {out_rel}  (custom page)")

    write(os.path.join(OUT, "404.html"), render("404.html", "", "none", header, footer))
    built.append("404.html")

    for out_rel, target in REDIRECTS.items():
        write(os.path.join(OUT, out_rel),
              finalize(REDIRECT_TEMPLATE.format(target=target, target_json=json.dumps(target))))

    urls = ["/", "/statement-of-faith/", "/messages/", "/contact/"] + [f"/{p['_slug']}/" for p in custom]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{CANONICAL_HOST}{BASE_PATH}{u}</loc></url>" for u in urls]
    sitemap.append("</urlset>")
    write(os.path.join(OUT, "sitemap.xml"), "\n".join(sitemap) + "\n")
    robots = ("User-agent: *\nDisallow: /\n" if NOINDEX else
              f"User-agent: *\nAllow: /\n\nSitemap: {CANONICAL_HOST}{BASE_PATH}/sitemap.xml\n")
    write(os.path.join(OUT, "robots.txt"), robots)

    for out_rel in built:
        txt = read(os.path.join(OUT, out_rel))
        if re.search(r"\{\{[A-Z_]+(:[a-z0-9_-]+)?\}\}", txt):
            errors.append(f"unresolved template token in {out_rel}")
    return report(len(built))


def report(count=0):
    if errors:
        print("\nBUILD STOPPED. Please fix:", file=sys.stderr)
        for e in errors:
            print("  -", e, file=sys.stderr)
        return 1
    print(f"\nDone. {count} pages written to site/")
    return 0


if __name__ == "__main__":
    sys.exit(build())
