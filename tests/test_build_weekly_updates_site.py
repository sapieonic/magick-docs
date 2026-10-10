#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_weekly_updates_site import write_site


class BuildWeeklyUpdatesSiteTest(unittest.TestCase):
    def test_builds_navigation_indexes_from_customer_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "weekly-updates"
            site = root / "_site"

            samarthya = source / "samarthya"
            bkb = source / "bkb" / "2026-08-07"
            samarthya.mkdir(parents=True)
            bkb.mkdir(parents=True)
            (source / "README.md").write_text("ignore me", encoding="utf-8")
            (samarthya / "2026-08-20.html").write_text(
                "<html><body>Samarthya 20</body></html>", encoding="utf-8"
            )
            (samarthya / "2026-08-14.html").write_text(
                "<html><body>Samarthya 14</body></html>", encoding="utf-8"
            )
            (bkb / "index.html").write_text(
                "<html><body>BKB 7</body></html>", encoding="utf-8"
            )

            customers = write_site(source, site)

            self.assertEqual([customer.name for customer in customers], ["bkb", "samarthya"])
            self.assertTrue((site / ".nojekyll").exists())
            self.assertTrue((site / "404.html").exists())
            self.assertFalse((site / "README.md").exists())

            copied = (site / "samarthya" / "2026-08-20.html").read_text(encoding="utf-8")
            self.assertIn("Samarthya 20", copied)

            home = (site / "index.html").read_text(encoding="utf-8")
            self.assertIn("Weekly updates", home)
            self.assertIn('href="samarthya/"', home)
            self.assertIn('href="samarthya/2026-08-20.html"', home)
            self.assertIn('href="bkb/2026-08-07/"', home)
            self.assertTrue(home.index("2026-08-20") < home.index("2026-08-14"))

            listing = (site / "index.txt").read_text(encoding="utf-8")
            self.assertIn("samarthya", listing)
            self.assertIn("/samarthya/2026-08-20.html", listing)
            self.assertIn("/bkb/2026-08-07/", listing)

            customer_index = (site / "samarthya" / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="../"', customer_index)
            self.assertIn('href="2026-08-20.html"', customer_index)
            self.assertNotIn("Samarthya 20", customer_index)

    def test_home_shows_latest_three_and_customer_page_groups_by_month(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "weekly-updates"
            site = root / "_site"

            acme = source / "acme"
            dates = ["2026-08-22", "2026-08-29", "2026-09-05", "2026-09-12", "2026-10-03"]
            for day in dates:
                folder = acme / day
                folder.mkdir(parents=True)
                (folder / "acme-health-review.html").write_text(
                    f"<html><body>{day}</body></html>", encoding="utf-8"
                )
            (acme / "notes.html").write_text("<html></html>", encoding="utf-8")
            small = source / "small"
            small.mkdir(parents=True)
            (small / "2026-10-03.html").write_text("<html></html>", encoding="utf-8")

            write_site(source, site)

            home = (site / "index.html").read_text(encoding="utf-8")
            for day in ["2026-10-03", "2026-09-12", "2026-09-05"]:
                self.assertIn(f'href="acme/{day}/acme-health-review.html"', home)
            for day in ["2026-08-29", "2026-08-22"]:
                self.assertNotIn(f"acme/{day}/", home)
            self.assertIn('href="acme/">Load more (3 older reports)</a>', home)
            self.assertEqual(home.count("Load more"), 1)

            customer_index = (site / "acme" / "index.html").read_text(encoding="utf-8")
            months = ["October 2026", "September 2026", "August 2026", "Undated"]
            positions = [customer_index.index(f"<summary>{month} ") for month in months]
            self.assertEqual(positions, sorted(positions))
            self.assertIn('<span class="count">2 reports</span>', customer_index)
            self.assertIn('<span class="count">1 report</span>', customer_index)
            self.assertNotIn("<details open", customer_index)
            for day in dates:
                self.assertIn(f'href="{day}/acme-health-review.html"', customer_index)
            self.assertIn('href="notes.html"', customer_index)

    def test_empty_source_still_writes_home_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "_site"
            write_site(root / "missing", site)
            home = (site / "index.html").read_text(encoding="utf-8")
            self.assertIn("No customer folders found yet", home)
            self.assertNotIn("<img", home)

    def test_copies_assets_and_shows_logo_on_landing_page_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "weekly-updates"
            assets = root / "assets"
            site = root / "_site"
            (source / "acme").mkdir(parents=True)
            (source / "acme" / "2026-10-03.html").write_text("<html></html>", encoding="utf-8")
            assets.mkdir()
            (assets / "magic-voice-logo.png").write_bytes(b"\x89PNG")

            write_site(source, site, assets)

            self.assertEqual((site / "assets" / "magic-voice-logo.png").read_bytes(), b"\x89PNG")
            home = (site / "index.html").read_text(encoding="utf-8")
            self.assertIn('<img src="assets/magic-voice-logo.png" alt="Magic Voice"', home)
            customer_index = (site / "acme" / "index.html").read_text(encoding="utf-8")
            self.assertNotIn("<img", customer_index)


if __name__ == "__main__":
    unittest.main()
