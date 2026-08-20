# Weekly updates

Drop raw HTML reports here. A GitHub Actions workflow publishes this directory to GitHub Pages on every merge to `main` that changes these files.

## Layout

```text
weekly-updates/
  <customer>/
    <date>.html
```

Examples:

```text
weekly-updates/samarthya/2026-08-20.html
weekly-updates/bkb/2026-08-14.html
weekly-updates/bkb/2026-08-07/index.html
```

Customer folder names become navigation headings. Dates in the file or folder name (`YYYY-MM-DD`, `YYYY_MM_DD`, or `YYYYMMDD`) are used for sorting and labels.

Do not commit `index.html` at the customer folder root. The publisher generates those pages so people can browse customers and dates.

Supporting files (CSS, images, JS) next to the HTML are copied as-is.
