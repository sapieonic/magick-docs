#!/usr/bin/env python3
"""Build a static GitHub Pages site from weekly-updates/.

Copies customer HTML as-is and generates text-style navigation indexes
so readers can find a customer and date without knowing the file path.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

SKIP_FILE_NAMES = {".gitkeep", "readme.md", "readme.txt"}
DATE_PATTERNS = [
    re.compile(r"(?P<y>\d{4})[-_ .](?P<m>\d{1,2})[-_ .](?P<d>\d{1,2})"),
    re.compile(r"(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})"),
]
HTML_SUFFIXES = {".html", ".htm"}
ROOT_REPORT_LIMIT = 3
SITE_ASSETS_DIR = "assets"
LOGO_FILE_NAME = "magic-voice-logo.png"


@dataclass(frozen=True)
class Report:
    href: str
    label: str
    sort_key: str
    source_relpath: str
    report_date: date | None = None


@dataclass
class Customer:
    name: str
    reports: list[Report] = field(default_factory=list)


def parse_date(text: str) -> date | None:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        try:
            return date(int(match["y"]), int(match["m"]), int(match["d"]))
        except ValueError:
            continue
    return None


def is_skipped_file(path: Path) -> bool:
    return path.name.lower() in SKIP_FILE_NAMES or path.name.startswith(".")


def report_from_html(customer_dir: Path, path: Path) -> Report | None:
    rel = path.relative_to(customer_dir)
    if rel.as_posix().lower() == "index.html":
        return None

    if path.name.lower() == "index.html":
        href = rel.parent.as_posix().rstrip("/") + "/"
        label_source = rel.parent.name
    else:
        href = rel.as_posix()
        label_source = path.stem

    parsed = parse_date(label_source) or parse_date(rel.as_posix())
    if parsed:
        label = parsed.isoformat()
        sort_key = f"{parsed.isoformat()}-{href.lower()}"
    else:
        label = label_source.replace("_", " ").replace("-", " ")
        sort_key = f"zzzz-{label.lower()}-{href.lower()}"

    return Report(
        href=href,
        label=label,
        sort_key=sort_key,
        source_relpath=rel.as_posix(),
        report_date=parsed,
    )


def collect_customers(source_dir: Path) -> list[Customer]:
    customers: list[Customer] = []
    if not source_dir.exists():
        return customers

    for child in sorted(source_dir.iterdir(), key=lambda p: p.name.lower()):
        if not child.is_dir() or child.name.startswith("."):
            continue

        reports: list[Report] = []
        for path in sorted(child.rglob("*")):
            if not path.is_file() or is_skipped_file(path):
                continue
            if path.suffix.lower() not in HTML_SUFFIXES:
                continue
            report = report_from_html(child, path)
            if report:
                reports.append(report)

        dated = [report for report in reports if report.report_date]
        undated = [report for report in reports if not report.report_date]
        dated.sort(key=lambda item: item.sort_key, reverse=True)
        undated.sort(key=lambda item: item.sort_key)
        customers.append(Customer(name=child.name, reports=dated + undated))

    return customers


def copy_source(source_dir: Path, site_dir: Path) -> None:
    if site_dir.exists():
        shutil.rmtree(site_dir)
    site_dir.mkdir(parents=True)

    if not source_dir.exists():
        return

    for item in source_dir.iterdir():
        if item.name.startswith(".") or item.name.lower() in SKIP_FILE_NAMES:
            continue
        destination = site_dir / item.name
        if item.is_dir():
            shutil.copytree(
                item,
                destination,
                ignore=shutil.ignore_patterns(".gitkeep", "README.md", "readme.md"),
            )
        elif item.suffix.lower() in HTML_SUFFIXES:
            shutil.copy2(item, destination)


def render_page(title: str, body: str, home_href: str | None = None) -> str:
    home_link = (
        f'<p class="back"><a href="{html.escape(home_href, quote=True)}">All customers</a></p>'
        if home_href
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --text: #1b1b1b;
      --muted: #555;
      --border: #d6d6d6;
      --link: #0b57d0;
    }}
    body {{
      margin: 0 auto;
      max-width: 52rem;
      padding: 2rem 1.25rem 4rem;
      font: 16px/1.5 ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
      color: var(--text);
    }}
    h1, h2 {{
      font-weight: 650;
      letter-spacing: -0.02em;
    }}
    h1 {{ margin: 0 0 0.35rem; font-size: 1.75rem; }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.9rem;
      margin-bottom: 0.35rem;
    }}
    .brand img {{ display: block; }}
    .brand h1 {{ margin: 0; }}
    h2 {{ margin: 1.75rem 0 0.5rem; font-size: 1.15rem; }}
    p, li {{ color: var(--text); }}
    .lede, .empty, .meta, .back {{ color: var(--muted); }}
    a {{ color: var(--link); }}
    .customer {{
      border-top: 1px solid var(--border);
      padding: 1rem 0 0.25rem;
    }}
    .customer:first-of-type {{ border-top: 0; padding-top: 0; }}
    ul {{
      list-style: none;
      margin: 0;
      padding: 0;
    }}
    li {{
      display: flex;
      gap: 1rem;
      padding: 0.2rem 0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.95rem;
    }}
    .date {{ min-width: 11ch; }}
    .path {{ color: var(--muted); }}
    .more {{ margin: 0.6rem 0 0; }}
    .more-button {{
      display: inline-block;
      padding: 0.3rem 0.8rem;
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 0.9rem;
      text-decoration: none;
    }}
    .more-button:hover {{ border-color: var(--link); }}
    .month {{
      border-top: 1px solid var(--border);
      padding: 0.6rem 0;
    }}
    .month:last-of-type {{ border-bottom: 1px solid var(--border); }}
    .month summary {{
      cursor: pointer;
      font-weight: 600;
    }}
    .month ul {{ margin-top: 0.5rem; }}
    .count {{
      color: var(--muted);
      font-weight: 400;
      font-size: 0.9rem;
      margin-left: 0.5rem;
    }}
  </style>
</head>
<body>
  {home_link}
  {body}
</body>
</html>
"""


def render_root_header(logo_href: str | None) -> str:
    if not logo_href:
        return "<h1>Weekly updates</h1>"
    return (
        '<header class="brand">'
        f'<img src="{html.escape(logo_href, quote=True)}" alt="Magic Voice" width="72" height="72">'
        "<h1>Weekly updates</h1>"
        "</header>"
    )


def render_root_index(
    customers: list[Customer], generated_at: str, logo_href: str | None = None
) -> str:
    header = render_root_header(logo_href)
    if not customers:
        body = f"""
  {header}
  <p class="lede">Customer reports published from <code>weekly-updates/</code>.</p>
  <p class="empty">No customer folders found yet. Add <code>weekly-updates/&lt;customer&gt;/&lt;date&gt;.html</code> and merge to main.</p>
"""
        return render_page("Weekly updates", body)

    sections = []
    for customer in customers:
        sections.append(
            render_customer_section(
                customer, href_prefix=f"{customer.name}/", limit=ROOT_REPORT_LIMIT
            )
        )

    body = f"""
  {header}
  <p class="lede">Choose a customer, then open the dated HTML report.</p>
  {"".join(sections)}
  <p class="meta">Generated {html.escape(generated_at)} from <code>weekly-updates/</code>.</p>
"""
    return render_page("Weekly updates", body)


def render_customer_index(customer: Customer, generated_at: str) -> str:
    heading = customer.name
    body = f"""
  <h1>{html.escape(heading)}</h1>
  <p class="lede">Dated weekly update pages for this customer, grouped by month.</p>
  {render_customer_months(customer)}
  <p class="meta">Generated {html.escape(generated_at)} from <code>weekly-updates/{html.escape(customer.name)}/</code>.</p>
"""
    return render_page(f"{heading} weekly updates", body, home_href="../")


def render_report_rows(reports: list[Report], href_prefix: str) -> str:
    rows = []
    for report in reports:
        href = f"{href_prefix}{report.href}"
        rows.append(
            "<li>"
            f'<span class="date"><a href="{html.escape(href, quote=True)}">{html.escape(report.label)}</a></span>'
            f'<span class="path">{html.escape(href)}</span>'
            "</li>"
        )
    return f"<ul>{''.join(rows)}</ul>"


def render_customer_section(
    customer: Customer, href_prefix: str, limit: int | None = None
) -> str:
    customer_href = html.escape(href_prefix, quote=True)
    heading_html = f'<h2><a href="{customer_href}">{html.escape(customer.name)}</a></h2>'
    if not customer.reports:
        items = '<p class="empty">No HTML reports in this folder yet.</p>'
    else:
        shown = customer.reports if limit is None else customer.reports[:limit]
        items = render_report_rows(shown, href_prefix)
        hidden = len(customer.reports) - len(shown)
        if hidden:
            noun = "report" if hidden == 1 else "reports"
            items += (
                f'<p class="more"><a class="more-button" href="{customer_href}">'
                f"Load more ({hidden} older {noun})</a></p>"
            )
    return f'<section class="customer">{heading_html}{items}</section>'


def group_by_month(reports: list[Report]) -> list[tuple[str, list[Report]]]:
    """Group newest-first reports into (month label, reports), undated last."""
    groups: dict[tuple[int, int] | None, list[Report]] = {}
    for report in reports:
        key = (
            (report.report_date.year, report.report_date.month)
            if report.report_date
            else None
        )
        groups.setdefault(key, []).append(report)

    dated = sorted((key for key in groups if key is not None), reverse=True)
    result = [
        (date(year, month, 1).strftime("%B %Y"), groups[(year, month)])
        for year, month in dated
    ]
    if None in groups:
        result.append(("Undated", groups[None]))
    return result


def render_customer_months(customer: Customer) -> str:
    if not customer.reports:
        return '<p class="empty">No HTML reports in this folder yet.</p>'

    months = []
    for label, reports in group_by_month(customer.reports):
        noun = "report" if len(reports) == 1 else "reports"
        months.append(
            '<details class="month">'
            f'<summary>{html.escape(label)} <span class="count">{len(reports)} {noun}</span></summary>'
            f"{render_report_rows(reports, href_prefix='')}"
            "</details>"
        )
    return f'<section class="months">{"".join(months)}</section>'


def render_text_index(customers: list[Customer], generated_at: str) -> str:
    lines = [
        "Weekly updates",
        "==============",
        "",
        "Customer / date listing. Open the matching HTML path on this site.",
        "",
    ]
    if not customers:
        lines.append("No customer folders found yet.")
        lines.append("")
        return "\n".join(lines)

    for customer in customers:
        lines.append(customer.name)
        if not customer.reports:
            lines.append("  (no HTML reports yet)")
        else:
            for report in customer.reports:
                lines.append(f"  {report.label:<12} /{customer.name}/{report.href}")
        lines.append("")
    lines.append(f"Generated {generated_at}")
    lines.append("")
    return "\n".join(lines)


def write_site(
    source_dir: Path, site_dir: Path, assets_dir: Path | None = None
) -> list[Customer]:
    customers = collect_customers(source_dir)
    copy_source(source_dir, site_dir)
    if assets_dir and assets_dir.is_dir():
        shutil.copytree(assets_dir, site_dir / SITE_ASSETS_DIR)
    logo_path = site_dir / SITE_ASSETS_DIR / LOGO_FILE_NAME
    logo_href = f"{SITE_ASSETS_DIR}/{LOGO_FILE_NAME}" if logo_path.is_file() else None
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    (site_dir / ".nojekyll").write_text("", encoding="utf-8")
    (site_dir / "index.html").write_text(
        render_root_index(customers, generated_at, logo_href), encoding="utf-8"
    )
    (site_dir / "index.txt").write_text(
        render_text_index(customers, generated_at), encoding="utf-8"
    )
    (site_dir / "404.html").write_text(
        render_page(
            "Not found",
            """
  <h1>Page not found</h1>
  <p class="lede">That weekly update URL does not exist. Start from the <a href="./">customer listing</a>.</p>
""",
        ),
        encoding="utf-8",
    )

    for customer in customers:
        customer_dir = site_dir / customer.name
        customer_dir.mkdir(parents=True, exist_ok=True)
        (customer_dir / "index.html").write_text(
            render_customer_index(customer, generated_at), encoding="utf-8"
        )

    return customers


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("weekly-updates"),
        help="Customer HTML source directory",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("_site"),
        help="Directory to write the GitHub Pages site into",
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=Path("assets"),
        help="Site-wide static files (logo) copied to <out>/assets/",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    customers = write_site(args.source, args.out, args.assets)
    sys.stdout.write(render_text_index(customers, "build"))
    sys.stdout.write(f"Wrote {args.out.resolve()}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
