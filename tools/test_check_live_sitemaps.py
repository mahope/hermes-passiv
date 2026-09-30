#!/usr/bin/env python3
import unittest
from email.message import Message

import check_live_sitemaps
from check_live_sitemaps import encoded_url, has_noindex_header, serving_domains

# De udleverede retry-tal, målt før nogen test patcher dem. `setUp` slår tempoet
# fra, så tallene skal læses her for at kunne dømmes som de udleveres.
SHIPPED_RETRY_ATTEMPTS = check_live_sitemaps.RETRY_ATTEMPTS
SHIPPED_RETRY_DELAY = check_live_sitemaps.RETRY_DELAY


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


class TransientRetryTests(unittest.TestCase):
    """Et netværksreset må ikke erklære en sund udgivelse for brudt.

    Kørsel `36763842986` døde i alle tre deploys på ét enkelt
    `<urlopen error [Errno 104] Connection reset by peer>` for en side der
    svarer 200 hver gang fra en maskine i samme øjeblik. Forsøg på ny kun
    *forbigående* fejl er derfor ikke en belønning af tålmodighed — det er
    forskellen på en rød port der betyder noget og en der lyder tilfældigt.
    """

    PAGE = (
        "<html><head><title>PrestaShop-tjek</title>"
        '<link rel="canonical" href="https://mahope.tools/guides/prestashop">'
        '<script type="application/ld+json">{"@context":"https://schema.org"}</script>'
        "</head><body>ok</body></html>"
    )

    ROBOTS = "User-agent: *\nAllow: /\n\nSitemap: https://mahope.tools/sitemap.xml\n"

    def setUp(self) -> None:
        self.calls: list[str] = []
        self.script: list = []
        original_fetch = check_live_sitemaps.fetch
        original_delay = check_live_sitemaps.RETRY_DELAY

        def fake_fetch(url: str, timeout: int = 30):
            self.calls.append(url)
            return self.script.pop(0) if self.script else (200, b"", None, None)

        check_live_sitemaps.fetch = fake_fetch
        # Rytmen læses fra modulet ved kald, så tempoet kan slås fra her i stedet
        # for at lappe `time.sleep` — det er ét delt modul for hele processen.
        check_live_sitemaps.RETRY_DELAY = 0.0
        self.addCleanup(lambda: setattr(check_live_sitemaps, "fetch", original_fetch))
        self.addCleanup(lambda: setattr(check_live_sitemaps, "RETRY_DELAY", original_delay))

    def test_a_reset_followed_by_200_passes_after_one_retry(self) -> None:
        self.script = [(None, b"", None, "[Errno 104] Connection reset by peer"), (200, b"ok", None, None)]
        self.assertEqual((200, b"ok", None, None), check_live_sitemaps.fetch_resilient("https://mahope.tools/"))
        self.assertEqual(2, len(self.calls))

    def test_a_5xx_is_retried(self) -> None:
        self.script = [(503, b"", None, None), (200, b"ok", None, None)]
        self.assertEqual(200, check_live_sitemaps.fetch_resilient("https://mahope.tools/")[0])
        self.assertEqual(2, len(self.calls))

    def test_a_persistent_reset_is_still_reported(self) -> None:
        """Et retry må aldrig gøre en ægte fejl grøn — kun forsinke den."""
        self.script = [(None, b"", None, "[Errno 104] Connection reset by peer")] * 5
        self.assertEqual(
            "[Errno 104] Connection reset by peer",
            check_live_sitemaps.fetch_resilient("https://mahope.tools/")[3],
        )
        self.assertEqual(3, len(self.calls))

    def test_a_404_is_not_retried(self) -> None:
        self.script = [(404, b"", None, None)]
        self.assertEqual(404, check_live_sitemaps.fetch_resilient("https://mahope.tools/")[0])
        self.assertEqual(1, len(self.calls))

    def test_a_429_is_not_retried(self) -> None:
        """429 er endelig per kontrakt — et forsøg mere ville bare forlænge den."""
        self.script = [(429, b"", None, None)]
        self.assertEqual(429, check_live_sitemaps.fetch_resilient("https://mahope.tools/")[0])
        self.assertEqual(1, len(self.calls))

    def test_a_200_is_fetched_once(self) -> None:
        self.assertEqual(200, check_live_sitemaps.fetch_resilient("https://mahope.tools/")[0])
        self.assertEqual(1, len(self.calls))

    def test_is_transient_classifies_by_contract(self) -> None:
        for status, error, expected in [
            (None, "timeout", True),
            (500, None, True),
            (502, None, True),
            (503, None, True),
            (200, None, False),
            (301, None, False),
            (403, None, False),
            (404, None, False),
            (429, None, False),
        ]:
            with self.subTest(status=status, error=error):
                self.assertEqual(expected, check_live_sitemaps.is_transient(status, error))

    # `fetch_resilient` kan være perfekt, og `check_page` kan alligevel kalde det
    # gamle `fetch`. Uden de tre side-tests dømmer klassen kun sig selv: mutationen
    # «check_page bruger fetch igen» var grøn på porten, som det viste sig da den
    # blev skrevet først. Her sker det faktiske kald — både `check_live_domain` og
    # `check_bugbottle_source` går gennem `check_page`.

    def test_a_page_behind_a_reset_is_still_checked(self) -> None:
        self.script = [
            (None, b"", None, "[Errno 104] Connection reset by peer"),
            (200, self.PAGE.encode("utf-8"), None, None),
        ]
        self.assertEqual(
            [],
            check_live_sitemaps.check_page("https://mahope.tools/guides/prestashop"),
        )
        self.assertEqual(2, len(self.calls))

    def test_a_page_that_stays_404_is_red_without_retrying(self) -> None:
        self.script = [(404, b"", None, None)]
        problems = check_live_sitemaps.check_page("https://mahope.tools/guides/prestashop")
        self.assertTrue(any("HTTP 404" in problem for problem in problems), str(problems))
        self.assertEqual(1, len(self.calls))

    def test_a_page_that_stays_down_is_red_after_the_attempts(self) -> None:
        self.script = [(None, b"", None, "[Errno 104] Connection reset by peer")] * 5
        problems = check_live_sitemaps.check_page("https://mahope.tools/guides/prestashop")
        self.assertTrue(any("Connection reset" in problem for problem in problems), str(problems))
        self.assertEqual(3, len(self.calls))

    def test_an_advertised_file_behind_a_reset_is_not_reported_missing(self) -> None:
        self.script = [
            (None, b"", None, "[Errno 104] Connection reset by peer"),
            (200, b"", None, None),
        ]
        self.assertEqual([], check_live_sitemaps.check_advertised_live("mahope.tools", self.ROBOTS))
        self.assertEqual(2, len(self.calls))

    def test_a_verified_route_behind_a_reset_passes(self) -> None:
        self.script = [
            (None, b"", None, "[Errno 104] Connection reset by peer"),
            (200, b"", None, None),
        ]
        problems, checked = check_live_sitemaps.check_route_live("/scan")
        self.assertEqual([], problems)
        self.assertEqual(["https://mahope.tools/scan"], checked)
        self.assertEqual(2, len(self.calls))

    def test_shipped_defaults_leave_room_between_attempts(self) -> None:
        """Rytmen er slået fra i `setUp`, så de udleverede tal dømmes her.

        Uden pause rammer et retry en 5xx fra Cloudflare tre gange i træk, og det
        er en fejl der ligner et angreb mere end en helbredelse.
        """
        self.assertGreater(SHIPPED_RETRY_DELAY, 0)
        self.assertGreaterEqual(SHIPPED_RETRY_ATTEMPTS, 2)
        self.assertLessEqual(SHIPPED_RETRY_ATTEMPTS, 5)

    def test_a_retired_download_behind_a_reset_is_not_called_reachable(self) -> None:
        """En tilbagetrukket fil må ikke meldes som hentbar på grund af et reset."""
        headers = Message()
        headers["Location"] = "https://cleancopy.tools/downloads/clean-copy-firefox-v1.5.4.zip"
        self.script = [
            (None, b"", None, "[Errno 104] Connection reset by peer"),
            (301, b"", headers, None),
        ]
        self.assertEqual([], check_live_sitemaps.check_retired_downloads_live("cleancopy.tools"))
        self.assertEqual(2, len(self.calls))

    def test_a_retired_download_that_is_reachable_is_still_red(self) -> None:
        self.script = [(200, b"", None, None)]
        problems = check_live_sitemaps.check_retired_downloads_live("cleancopy.tools")
        self.assertTrue(any("HTTP 200" in problem for problem in problems), str(problems))
        self.assertEqual(1, len(self.calls))


if __name__ == "__main__":
    unittest.main()
