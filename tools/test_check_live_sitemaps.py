#!/usr/bin/env python3
import unittest
from email.message import Message

import check_live_sitemaps
from check_live_sitemaps import encoded_url, has_noindex_header, serving_domains


class LiveSitemapTests(unittest.TestCase):
    def test_unicode_path_is_percent_encoded(self) -> None:
        self.assertEqual(
            "https://cleancopy.tools/da/blog/inds%C3%A6t-i-obsidian-ren-markdown",
            encoded_url("https://cleancopy.tools/da/blog/indsæt-i-obsidian-ren-markdown"),
        )

    def test_existing_query_and_fragment_are_safe(self) -> None:
        self.assertEqual(
            "https://mahope.tools/da/?q=%C3%A6",
            encoded_url("https://mahope.tools/da/?q=æ#ignored"),
        )

    def test_x_robots_noindex_is_rejected(self) -> None:
        headers = Message()
        headers["X-Robots-Tag"] = "index, follow"
        self.assertFalse(has_noindex_header(headers))
        headers.replace_header("X-Robots-Tag", "noindex, follow")
        self.assertTrue(has_noindex_header(headers))


class AdvertisedFileTests(unittest.TestCase):
    """robots.txt skal ikke kun pege korrekt — de filer den peger på skal findes."""

    ROBOTS = (
        "User-agent: *\nAllow: /\n\nSitemap: https://mahope.tools/sitemap.xml\n"
        "# Machine-readable summary for AI assistants: https://mahope.tools/llms.txt\n"
    )

    def setUp(self) -> None:
        self.requested: list[str] = []
        self.statuses: dict[str, int] = {}
        original = check_live_sitemaps.fetch

        def fake_fetch(url: str, timeout: int = 30):
            self.requested.append(url)
            return self.statuses.get(url, 200), b"", None, None

        check_live_sitemaps.fetch = fake_fetch
        self.addCleanup(lambda: setattr(check_live_sitemaps, "fetch", original))

    def test_all_advertised_files_resolving_200_passes(self) -> None:
        self.assertEqual([], check_live_sitemaps.check_advertised_live("mahope.tools", self.ROBOTS))
        self.assertEqual(
            ["https://mahope.tools/llms.txt", "https://mahope.tools/sitemap.xml"],
            self.requested,
        )

    def test_advertised_file_missing_in_production_fails(self) -> None:
        self.statuses["https://mahope.tools/llms.txt"] = 404
        problems = check_live_sitemaps.check_advertised_live("mahope.tools", self.ROBOTS)
        self.assertTrue(any("llms.txt" in problem and "HTTP 404" in problem for problem in problems))


class ServingDomainTests(unittest.TestCase):
    """En rute skal verificeres på det domæne der faktisk serverer den.

    De fire sites deler ét `site/`-træ, og `build_sites.SITES` fordeler
    filerne pr. domæne, så `/url-to-markdown` er en cleancopy-rute selv om
    andre sider linker til den rod-relative. Verificeret på mahope.tools
    svarer den 404 og læses som en brudt udgivelse.
    """

    def test_markdown_tool_resolves_to_cleancopy(self) -> None:
        self.assertEqual(
            ["cleancopy.tools"],
            serving_domains("/url-to-markdown"),
        )

    def test_danish_mirror_resolves_to_cleancopy(self) -> None:
        self.assertEqual(
            ["cleancopy.tools"],
            serving_domains("/da/url-til-markdown"),
        )

    def test_mahope_route_resolves_to_mahope(self) -> None:
        self.assertEqual(["mahope.tools"], serving_domains("/scan"))

    def test_unknown_route_has_no_domain(self) -> None:
        self.assertEqual([], serving_domains("/no-such-route-here"))

    def test_full_url_and_trailing_slash_normalize(self) -> None:
        self.assertEqual(
            serving_domains("/url-to-markdown"),
            serving_domains("https://cleancopy.tools/url-to-markdown"),
        )
        self.assertEqual(
            serving_domains("/books"),
            serving_domains("/books/"),
        )

    def test_unicode_route_is_decoded_before_lookup(self) -> None:
        # Inventaret gemmer den decodede sti; en kodet URL skal finde den.
        self.assertEqual(
            ["mahope.tools"],
            serving_domains("/da/blog/inds%C3%A6t-uden-formatering-i-chrome"),
        )


if __name__ == "__main__":
    unittest.main()
