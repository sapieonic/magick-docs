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

    def test_empty_source_still_writes_home_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "_site"
            write_site(root / "missing", site)
            home = (site / "index.html").read_text(encoding="utf-8")
            self.assertIn("No customer folders found yet", home)


if __name__ == "__main__":
    unittest.main()
