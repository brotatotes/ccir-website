# Christian Church In Raleigh — website

A simple, fast, static website for **Christian Church In Raleigh**.
No accounts, no database, no tracking, no paid services. It's just HTML, CSS,
a tiny bit of JavaScript, and some images — the kind of site that will keep
working for many years with very little maintenance.

- **Live address (during review):** https://ccir.brotatotes.com
- **Pages:** Home · Statement of Faith · Sunday Messages · Contact
- **Hosting:** GitHub Pages (free)

---

## The quick version (for whoever maintains this)

You do **not** need to be a programmer, and you do **not** need any AI tool to
update this site. Almost every change is just editing text in a file.

Everything visitors see is built from the files in the **`src/`** folder.
When you change something there, you run **one command** to rebuild, and the
finished website appears in the **`site/`** folder, which is what gets published.

```
src/pages/       <- the four pages (edit these)
src/partials/    <- the shared menu (header) and footer, edited once
site/            <- the finished website (generated — don't hand-edit pages here)
build.py         <- the one command that assembles the site
tests/           <- automatic checks that catch mistakes
```

---

## How to make a change

### 1. Install nothing but Python
The build uses only Python 3, which is already on Mac and Linux. On Windows,
install it from https://python.org (check "Add to PATH"). That's the only tool.

### 2. Edit the text
Open the file you want to change in any text editor (even Notepad or TextEdit):

| To change…                        | Edit this file                          |
|-----------------------------------|-----------------------------------------|
| Home page                         | `src/pages/index.html`                  |
| Statement of Faith                | `src/pages/statement-of-faith.html`     |
| Sunday Messages (videos)          | `src/pages/messages.html`               |
| Contact info / meeting times      | `src/pages/visit.html`                  |
| The top menu (all pages)          | `src/partials/header.html`              |
| The footer (all pages)            | `src/partials/footer.html`              |

Text lives between the tags, e.g. `<p>Sundays at 10:00 AM</p>`. Change the words
between `>` and `<` and leave the tags alone.

### 3. Rebuild
From this folder, run:

```bash
python3 build.py
```

You'll see it write the four pages plus the redirect pages into `site/`.

### 4. Check your work
```bash
python3 tests/check_site.py
```
If it says **"All checks passed ✅"** you're good. If it lists a problem, it will
tell you exactly what to fix (a broken link, a missing image, etc.).

### 5. Preview it locally (optional but recommended)
```bash
python3 -m http.server -d site 8000
```
Then open http://localhost:8000 in your browser. Press `Ctrl+C` to stop.

### 6. Publish
Commit and push to the `main` branch on GitHub. A GitHub Action automatically
rebuilds, runs the checks, and publishes the site within a minute or two. If the
checks fail, it will **not** publish — so a mistake can't take the site down.

---

## Common tasks

### Add a new Sunday message video
1. Upload the video to the church's YouTube channel (**@CCIR_**) as usual.
2. Copy its video ID — the part after `watch?v=` in the URL. For
   `https://www.youtube.com/watch?v=abc123XYZ` the ID is `abc123XYZ`.
3. Save a thumbnail so the site stays fast and private. From this folder:
   ```bash
   curl -s -o site/assets/img/thumbs/abc123XYZ.jpg \
     "https://i.ytimg.com/vi/abc123XYZ/hqdefault.jpg"
   ```
4. In `src/pages/messages.html`, copy one existing `<article class="video-card">…</article>`
   block, paste it as a new first item, and replace the video ID (it appears in
   `data-yt`, the thumbnail `src`/`srcset`, the `watch?v=` link) and the title text.
5. `python3 build.py && python3 tests/check_site.py`, then publish.

### Update a service time or contact detail
Edit `src/pages/visit.html` (and `src/pages/index.html` if it appears on the home
page too), rebuild, and publish. The footer email/place lives in
`src/partials/footer.html`.

### Turn on the contact form (about 5 minutes, no coding)
The contact form on **Contact** is intentionally switched off right now,
so no visitor message is ever silently lost. To make it live with a free
[Formspree](https://formspree.io) account:

1. Sign up at https://formspree.io (free tier is fine).
2. Create a new form that delivers to **christianchurchinraleigh@gmail.com**.
   Formspree gives you an endpoint like `https://formspree.io/f/abcdwxyz`.
3. Open `src/pages/visit.html` and find the `<form data-demo="true" …>` tag. Then:
   - change it to `<form action="https://formspree.io/f/abcdwxyz" method="POST">`
     (paste your real endpoint, and remove `data-demo="true"`);
   - delete the orange notice block just above the form
     (`<div class="form-note"> … </div>`) and the long HTML comment that explains
     these steps;
   - remove the word `disabled` from each `<input>`, the `<textarea>`, and the
     submit `<button>` (and drop `aria-disabled="true"` on the button).
4. `python3 build.py && python3 tests/check_site.py` and publish.
   (The checks assume the form is in demo mode; once it's live, update or remove
   the "contact form is disabled/demo" checks in `tests/check_site.py`.)

---

## What's under the hood (for the curious)

- **No framework.** Plain HTML/CSS/JS. `build.py` is ~100 lines of standard
  Python and just glues the shared header/footer into each page and marks the
  current menu item. There is nothing to `npm install`.
- **Fonts** (Montserrat + Inter) are self-hosted in `site/assets/fonts/` so the
  site doesn't depend on Google and loads fast.
- **Photos** are the church's own images, resized and served as WebP with JPEG
  fallbacks in `site/assets/img/`. All camera metadata (including GPS location)
  was stripped for privacy.
- **Sunday message videos** stay on YouTube. The page shows a self-hosted
  thumbnail and only loads YouTube (via the privacy-friendly
  `youtube-nocookie.com`) after a visitor clicks play.
- **Old links keep working:** `/about-2` and `/about-3` redirect to
  `/statement-of-faith/`, `/visit` and `/visit-us` redirect to `/contact/`, and `/messages`
  is kept as-is.
- **Design system** lives in `site/assets/styles.css` (navy `#3f4359` / off-white
  identity, responsive layout, accessible focus states, reduced-motion support).

## Colophon
Content is migrated from the church's existing site. No church facts were
invented. Brand palette and typography direction are documented in
`../SOURCE_INVENTORY.md` and `../PROJECT_DECISIONS.md` (kept one level up).
