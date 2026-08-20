# magick-docs

Customer weekly update HTML is published to GitHub Pages from `weekly-updates/`.

## Add a report

Put a raw HTML file under the customer folder, named by date:

```text
weekly-updates/<customer>/<YYYY-MM-DD>.html
```

Merge that change to `main`. The [Deploy weekly updates](.github/workflows/deploy-weekly-updates.yml) workflow copies the HTML, generates a text-style index of customers and dates, and deploys the site.

## Enable GitHub Pages

The deploy job uses `actions/configure-pages` with `enablement: true` so it will try to turn Pages on if it is not already enabled.

That flag cannot use the default `GITHUB_TOKEN`. Add a repository secret named `PAGES_ENABLE_TOKEN`:

- Personal access token: `repo` scope, or fine-grained **Pages: Write**
- GitHub App token: `administration:write` and `pages:write`

Without that secret, enable Pages once in **Settings → Pages** and set **Source** to **GitHub Actions**.

The site URL for this repository is `https://sapieonic.github.io/magick-docs/`. The same listing is also available as plain text at `/index.txt`.
