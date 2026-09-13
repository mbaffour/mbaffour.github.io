# mbaffour.github.io

Personal research site of Michael Baffour Awuah, served by GitHub Pages straight from
this repository. No build step is required to publish; two small scripts keep the
generated files honest.

## Layout

| Path | What it is |
|---|---|
| `index.html` | The research site: hero, research focus, publications, software, teaching, blog band, gallery, contact. |
| `blog/index.html` | The full blog listing with search and tag filters. |
| `blog/<slug>.html` | One self-contained page per post. |
| `journey.html`, `builds.html` | The long-form story and the non-research side builds. |
| `structure-viewer/` | Hosted copy of the [Protein Structure Viewer](https://github.com/mbaffour/protein-structure-viewer); copy its `index.html` here on each release. |
| `assets/js/posts-data.js` | **The single source of truth for posts.** Read by the homepage band, the command palette, the blog index, every post page and the generator below. |
| `assets/js/builds-data.js` | The same for side builds. |
| `assets/js/post.js` | Adds the byline bar, table of contents and previous/next links to every post at load. |
| `scripts/build-site.mjs` | Writes `feed.xml` and `sitemap.xml` from the data and git history. |
| `scripts/check-links.mjs` | Fails if any relative link or asset reference on the site points nowhere. |

## Adding a post

1. Write `blog/<slug>.html` (copy the nearest existing post as a starting point; keep the
   two `<script>` tags before `</body>`).
2. Add an entry at the top of `assets/js/posts-data.js`: `title`, `date`, `iso`, `tags`,
   `blurb`, `url`, optionally `image`/`imageAlt`. When you revise a post later, set `updated`.
3. Run the generator and the link check, then commit everything it changed:

```bash
node scripts/build-site.mjs && node scripts/check-links.mjs
```

## Checks before pushing

- `node scripts/check-links.mjs` — no broken internal references.
- Open the homepage, `blog/`, and the new post at a phone width; check dark and light.
- The factual record for the site and CV lives in `DISCREPANCIES.md`; anything that
  changes a date, count or title should agree with it.
