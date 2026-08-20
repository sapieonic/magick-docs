# magick-docs

Customer weekly update HTML is published to GitHub Pages from `weekly-updates/`.

## Add a report

Put a raw HTML file under the customer folder, named by date:

```text
weekly-updates/<customer>/<YYYY-MM-DD>.html
```

Merge that change to `main`. The [Deploy weekly updates](.github/workflows/deploy-weekly-updates.yml) workflow copies the HTML, generates a text-style index of customers and dates, and deploys the site.

## Enable GitHub Pages

One-time repository setting:

1. Open **Settings → Pages**.
2. Set **Source** to **GitHub Actions**.

The site URL for this repository is `https://sapieonic.github.io/magick-docs/`. The same listing is also available as plain text at `/index.txt`.
