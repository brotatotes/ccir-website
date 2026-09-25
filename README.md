# Christian Church In Raleigh — website

A simple, fast, static website for **Christian Church In Raleigh**, hosted free on GitHub Pages.

- **Live address (during review):** https://ccir.brotatotes.com
- **Pages:** Home · Statement of Faith · Sunday Messages · Contact, plus any extra pages added in the editor

## Editing content (no coding needed)

Two editors are set up side by side for comparison. Both edit the same content files.

**Sveltia CMS** at https://ccir.brotatotes.com/admin/ runs from this site itself, with no outside
service. Editors need a GitHub account with access to this repository and sign in with an access
token (the sign-in screen links to GitHub with the right permissions pre-selected).

**Pages CMS** at https://app.pagescms.org is a hosted editor.

1. Sign in. Editors without GitHub can be invited by email from **Collaborators** in the sidebar.
2. Pick what to change: Home page, Sunday Messages, Statement of Faith, Contact page, Extra pages, or Footer & site settings.
3. Click **Save**. The site rebuilds and goes live in about a minute.

**Extra pages** can be created, reordered and built from sections such as text, photo with text,
columns, a YouTube video, or an invitation banner with a button. Tick "Show in the top menu" to add
the page to the navigation.

## Where things live

```
content/            <- all words, photos and videos (what the editor changes)
content/pages/      <- extra pages created in the editor
src/templates/      <- page designs
src/partials/       <- shared header, footer and contact form
static/             <- styles, fonts, images, favicon, CNAME (copied as-is)
.pages.yml          <- Pages CMS forms
static/admin/       <- Sveltia CMS (editor app and config.yml forms)
build.py            <- turns content + templates into the finished site
tests/check_site.py <- automatic checks run before every publish
```

The `site/` folder is generated and not stored in the repository.

## Building locally

Python 3 and the Markdown package are required.

```bash
pip install -r requirements.txt
python3 build.py
python3 tests/check_site.py
```

Every push to `main`, including every Save in the editor, runs the same build and checks on GitHub.
If a check fails, the previous version of the site stays live.

## Contact form

The form is disabled until a Formspree endpoint is connected. See the notes inside
`src/partials/contact-form.html`.
