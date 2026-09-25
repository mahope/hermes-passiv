#!/usr/bin/env python3
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import check_sitemaps


class SitemapCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.domain = "mahope.tools"
        self.inventory = {"mahope.tools": ("/", "/free-tools")}
        self.dist = self.root / self.domain
        self.dist.mkdir()
        self.write_html("index.html", "https://mahope.tools/", index=True)
        self.write_html("free-tools.html", "https://mahope.tools/free-tools", index=True)
        self.write_html("hidden/index.html", "https://mahope.tools/hidden/", index=False)
        self.write_robots()
        self.write_sitemap(["https://mahope.tools/", "https://mahope.tools/free-tools"])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_html(self, relative: str, canonical: str, index: bool, http_equiv: bool = False) -> None:
        path = self.dist / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        robots = "index,follow" if index else "noindex,follow"
        attribute = "http-equiv" if http_equiv else "name"
        path.write_text(
            f'<!doctype html><html><head><link rel="canonical" href="{canonical}">'
            f'<meta {attribute}="robots" content="{robots}"></head><body></body></html>',
            encoding="utf-8",
        )

    def write_robots(self) -> None:
        (self.dist / "robots.txt").write_text(
            "User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: https://mahope.tools/sitemap.xml\n",
            encoding="utf-8",
        )

    def write_sitemap(self, urls: list[str]) -> None:
        entries = "".join(f"  <url><loc>{url}</loc></url>\n" for url in urls)
        data = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{entries}</urlset>\n"
        ).encode()
        (self.dist / "sitemap.xml").write_bytes(data)
        build_info = {
            "version": 1,
            "domain": self.domain,
            "commit": "a" * 40,
            "sitemap_count": len(urls),
            "sitemap_sha256": hashlib.sha256(data).hexdigest(),
            "routes_sha256": check_sitemaps.route_digest(urls),
        }
        (self.dist / "build-info.json").write_text(json.dumps(build_info, sort_keys=True) + "\n", encoding="utf-8")

    def test_valid_inventory(self) -> None:
        self.assertEqual([], check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory))

    def test_wrong_domain_fails(self) -> None:
        self.write_sitemap(["https://wrong.example/"])
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory)
        self.assertTrue(any("invalid sitemap URL" in problem for problem in problems))

    def test_duplicate_sitemap_url_fails(self) -> None:
        self.write_sitemap(["https://mahope.tools/", "https://mahope.tools/"])
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory)
        self.assertTrue(any("duplicate sitemap URL" in problem for problem in problems))

    def test_missing_canonical_route_fails(self) -> None:
        self.write_sitemap([])
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory)
        self.assertTrue(any("canonical route missing from sitemap" in problem for problem in problems))

    def test_free_tools_retention_fails(self) -> None:
        (self.dist / "free-tools.html").unlink()
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory)
        self.assertTrue(any("required route missing /free-tools" in problem for problem in problems))

    def test_http_equiv_noindex_and_htm_are_excluded(self) -> None:
        self.write_html("legacy.htm", "https://mahope.tools/legacy.htm", index=False, http_equiv=True)
        self.assertEqual([], check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory))

    def test_redirect_only_trailing_slash_fails(self) -> None:
        url = "https://mahope.tools/blog/cookie-consent-gdpr-2026/"
        self.write_html("blog/cookie-consent-gdpr-2026/index.html", url, index=True)
        self.write_sitemap(["https://mahope.tools/", "https://mahope.tools/free-tools", url])
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory)
        self.assertTrue(any("redirect-only route is indexable" in problem for problem in problems))

    def test_slash_equivalent_routes_fail(self) -> None:
        self.write_html("foo.html", "https://mahope.tools/foo", index=True)
        self.write_html("foo/index.html", "https://mahope.tools/foo/", index=True)
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory)
        self.assertTrue(any("slash-equivalent" in problem for problem in problems))

    def test_inventory_requires_missing_route(self) -> None:
        self.inventory["mahope.tools"] = ("/", "/free-tools", "/must-exist")
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory)
        self.assertTrue(any("inventory route has no indexable canonical HTML" in problem for problem in problems))

    def test_inventory_rejects_new_route(self) -> None:
        self.write_html("new.html", "https://mahope.tools/new", index=True)
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory)
        self.assertTrue(any("not in inventory" in problem for problem in problems))

    def test_expected_commit_mismatch_fails(self) -> None:
        problems = check_sitemaps.check_domain(self.domain, self.root, inventory=self.inventory, expected_commit="b" * 40)
        self.assertTrue(any("expected" in problem and "commit" in problem for problem in problems))


if __name__ == "__main__":
    unittest.main()
