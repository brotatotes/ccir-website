#!/usr/bin/env python3
"""
Automated checks for the Christian Church In Raleigh static site.

Run:  python3 tests/check_site.py
Exit code 0 = all checks pass. Non-zero = something to fix.

These are deliberately dependency-free (Python stdlib + html.parser) so they
run anywhere, including GitHub Actions, with no install step.

They verify:
  * the build output exists and is well-formed enough to serve;
  * every internal link/asset reference resolves to a real file;
  * accessibility basics (lang, one <h1>, alt text, skip link, labels);
  * the required content actually shipped (all 9 faith points, 8 videos,
    real contact email, meeting place, no leftover Wix placeholder junk);
  * the contact form is safely in disabled/demo mode (no live action);
  * legacy redirects and deploy files (CNAME, sitemap, etc.) are present.
"""
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

failures = []
passes = 0


def check(cond, msg):
    global passes
    if cond:
        passes += 1
    else:
        failures.append(msg)


def read(rel):
    with open(os.path.join(SITE, rel), "r", encoding="utf-8") as f:
        return f.read()


def exists(rel):
    return os.path.exists(os.path.join(SITE, rel))


# ---------------------------------------------------------------- parser
class Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.h1 = 0
        self.imgs = []            # list of dicts of attrs
        self.links = []           # href values
        self.assets = []          # src/href asset refs
        self.labels_for = set()
        self.input_ids = []
        self.has_lang = False
        self.has_skip = False
        self.title = None
        self._in_title = False
        self.meta_desc = None
        self.iframes = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if tag == "html" and a.get("lang"):
            self.has_lang = True
        if tag == "title":
            self._in_title = True
        if tag == "h1":
            self.h1 += 1
        if tag == "img":
            self.imgs.append(a)
            if a.get("src"):
                self.assets.append(a["src"])
            srcset = a.get("srcset")
        if tag == "source" and a.get("srcset"):
            for part in a["srcset"].split(","):
                url = part.strip().split(" ")[0]
                if url:
                    self.assets.append(url)
        if tag == "a":
            if a.get("href"):
                self.links.append(a["href"])
            if "skip-link" in (a.get("class") or ""):
                self.has_skip = True
        if tag in ("link", "script") and a.get("href"):
            self.assets.append(a["href"])
        if tag == "link" and a.get("href"):
            self.assets.append(a["href"])
        if tag == "script" and a.get("src"):
            self.assets.append(a["src"])
        if tag == "label" and a.get("for"):
            self.labels_for.add(a["for"])
        if tag in ("input", "textarea") and a.get("id"):
            self.input_ids.append((a.get("id"), a))
        if tag == "meta" and a.get("name") == "description":
            self.meta_desc = a.get("content")
        if tag == "iframe":
            self.iframes.append(a)

    def handle_data(self, data):
        if self._in_title and data.strip():
            self.title = data.strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False


def parse(rel):
    p = Extractor()
    p.feed(read(rel))
    return p


# ---------------------------------------------------------------- 1. build present
PAGES = ["index.html", "statement-of-faith/index.html",
         "messages/index.html", "contact/index.html", "404.html"]
for pg in PAGES:
    check(exists(pg), f"missing built page: {pg}")

# stop early if core pages missing
if failures:
    print("FAIL (pre-check):")
    for f in failures:
        print("  -", f)
    sys.exit(1)

# ---------------------------------------------------------------- 2. per-page structural + a11y
for pg in PAGES:
    doc = parse(pg)
    check(doc.has_lang, f"[{pg}] <html> missing lang attribute")
    check(doc.h1 == 1, f"[{pg}] expected exactly one <h1>, found {doc.h1}")
    check(doc.title, f"[{pg}] missing <title>")
    check(doc.has_skip, f"[{pg}] missing skip-link")
    # every img has alt attribute (may be empty for decorative)
    for img in doc.imgs:
        check("alt" in img, f"[{pg}] <img src={img.get('src')}> missing alt attribute")
    # every form input/textarea has a matching label
    for iid, attrs in doc.input_ids:
        check(iid in doc.labels_for, f"[{pg}] form field #{iid} has no <label for>")

# meta description on the four content pages
for pg in PAGES[:4]:
    doc = parse(pg)
    check(bool(doc.meta_desc and len(doc.meta_desc) > 40),
          f"[{pg}] meta description missing or too short")

# ---------------------------------------------------------------- 3. internal links & assets resolve
def resolve(ref):
    ref = ref.split("#")[0].split("?")[0]
    if not ref or ref.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
        return None
    if ref.startswith("/"):
        path = ref.lstrip("/")
    else:
        return None  # site uses root-relative only
    if ref.endswith("/"):
        path = os.path.join(path, "index.html")
    return path

for pg in PAGES:
    doc = parse(pg)
    for ref in doc.links + doc.assets:
        target = resolve(ref)
        if target is None:
            continue
        check(exists(target), f"[{pg}] broken internal reference: {ref} -> {target}")

# ---------------------------------------------------------------- 4. required content
faith = read("statement-of-faith/index.html")
for n in ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]:
    check(f">{n}<" in faith, f"[faith] missing point label: {n}")
# a few verbatim anchor phrases
for phrase in ["Triune God", "propitiation of our sins", "life giving Spirit",
               "infallible Word of God", "born under sin", "grace, not works",
               "masterpiece of God", "one baptism"]:
    check(phrase in faith, f"[faith] missing expected text: {phrase!r}")

msgs = read("messages/index.html")
VIDEO_IDS = ["brYjJuQpb78", "028NHl--m7Y", "JJqFPRXxdL0", "f_GsQJdqbpk",
             "u4ATLIqxQVI", "UFvli50BBb4", "E0B1lYP3DHo", "jko1U2Uik8k"]
for vid in VIDEO_IDS:
    check(vid in msgs, f"[messages] missing YouTube id: {vid}")
    check(exists(f"assets/img/thumbs/{vid}.jpg"), f"[messages] missing self-hosted thumbnail: {vid}.jpg")
# lite embeds should NOT ship a hard-coded youtube iframe in the HTML (privacy/perf)
check("<iframe" not in msgs, "[messages] iframe should be injected by JS, not present in HTML")
check("youtube-nocookie.com" in read("assets/main.js"), "[js] should use youtube-nocookie embeds")

home = read("index.html")
check("christianchurchinraleigh@gmail.com" in read("contact/index.html"), "[contact] missing contact email")
check("MLK Pkwy" in read("contact/index.html"), "[contact] missing meeting place")
check("10:00 AM" in home or "10AM" in home, "[home] missing Sunday service time")
for phrase in ["plan your visit", "plan a visit", "visit &amp; contact"]:
    check(phrase not in "\n".join(read(pg).lower() for pg in PAGES),
          f"site still contains unwanted visit-planning language: {phrase!r}")

# ---------------------------------------------------------------- 5. NO Wix placeholder leakage
for pg in PAGES:
    txt = read(pg).lower()
    for bad in ["500 terry francine", "info@mysite.com", "1800-000-000",
                "lorem ipsum", "i'm a paragraph", "wixstatic", "thanks for submitting"]:
        check(bad not in txt, f"[{pg}] contains placeholder/Wix leftover: {bad!r}")

# ---------------------------------------------------------------- 6. contact form is disabled/demo
visit = read("contact/index.html")
check('data-demo="true"' in visit, "[contact] contact form not marked demo")
check("formspree" in visit.lower(), "[contact] no Formspree guidance in contact form")
# form must not POST anywhere yet
check(not re.search(r'<form[^>]*\baction=', visit), "[contact] demo form should have no action= yet")
check(visit.count("disabled") >= 4, "[contact] demo form fields/button should be disabled")

# ---------------------------------------------------------------- 7. deploy + redirect files
for f in ["robots.txt", "sitemap.xml", "site.webmanifest",
          ".nojekyll", "favicon.ico"]:
    check(exists(f), f"missing deploy file: {f}")
if exists("CNAME"):
    check(read("CNAME").strip() == "ccir.brotatotes.com", "CNAME must be ccir.brotatotes.com")

for legacy, target in [("about-2/index.html", "/statement-of-faith/"),
                       ("about-3/index.html", "/statement-of-faith/"),
                       ("visit/index.html", "/contact/"),
                       ("visit-us/index.html", "/contact/")]:
    check(exists(legacy), f"missing legacy redirect: {legacy}")
    if exists(legacy):
        r = read(legacy)
        check(target in r, f"[{legacy}] does not point to {target}")
        check("http-equiv=\"refresh\"" in r, f"[{legacy}] missing meta refresh")

# /messages is the canonical path (legacy path preserved natively)
check(exists("messages/index.html"), "legacy /messages path not preserved")

# ---------------------------------------------------------------- report
print(f"\n{passes} checks passed, {len(failures)} failed.\n")
if failures:
    print("FAILURES:")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("All checks passed. ✅")
sys.exit(0)
