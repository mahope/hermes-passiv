#!/usr/bin/env python3
"""Selvtest for den ene regel om hvad der må prøves igen.

Opgave 32. `weekly_report.py` og `check_live_sitemaps.py` havde hver sin
`_transient` og var **uenige om 429** — den ene prøvede den igen, den anden
gjorde ikke. Det er dømt ved *opførsel*, ikke ved at læse koden: testen kalder
det begge scripts faktisk bruger, og sammenligner svarene.

De tre ting der skal være sande:

1. **Ét sted afgør det.** `check_live_sitemaps.is_transient` er præcis den
   funktion der ligger i `tools/transient.py`. Uden den ville porten kunne
   få sin egen regel igen, og de to ville glide fra hinanden i stedet for at
   slå.
2. **Ingen af de to scripts dømmer 429 selv.** Kilden læses, og ingen linje uden
   `#`-kommentar må indeholde tallet. Den afgørelse ligger i modulet — ellers er
   opgaven ikke løst, kun flyttet.
3. **Begge kaldersteder adfærder sig ens.** Et 503 prøves igen, et 429 ikke, i
   begge scripts. Beviset er antallet af `urlopen`-kald, ikke returværdien.

Sidste punkt er det, der ville have fanget originalfejlen: `http_json` returnerer
i begge tilfælde en undtagelse, så en test på returværdien kan ikke se
forskellen.

    python3 tools/test_transient.py
"""
from __future__ import annotations

import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_live_sitemaps  # noqa: E402
import transient  # noqa: E402
import weekly_report as report  # noqa: E402

TOOLS = Path(__file__).resolve().parent

# Fejlteksten fra `check_live_sitemaps.fetch` ved et netværksreset. Den er med,
# fordi det er den *anden* form af input: de to scripts kalder `is_transient`
# hver med sin egen, og de skal give samme svar på hver især.
RESET = "[Errno 104] Connection reset by peer"


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://x/api/stats", code, "nope", {}, None)


class OnePlaceTests(unittest.TestCase):
    def test_the_sitemap_port_uses_the_shared_function(self) -> None:
        # Identitet, ikke lighed. En lokal `def is_transient` i porten ville
        # være lige så korrekt at læse og lige så forkert at have.
        self.assertIs(transient.is_transient, check_live_sitemaps.is_transient)

    def test_neither_script_judges_429_itself(self) -> None:
        for name in ("check_live_sitemaps.py", "weekly_report.py"):
            with self.subTest(script=name):
                decisions = [
                    line for line in (TOOLS / name).read_text(encoding="utf-8").splitlines()
                    if "429" in line and not line.strip().startswith("#")
                ]
                self.assertEqual([], decisions, f"{name} dømmer 429 selv: {decisions}")

    def test_the_rationale_lives_with_the_decision(self) -> None:
        # Modulet skal sige *hvorfor* 429 er endelig, ellers er næste afløser
        # lige så tilfældig som den her var.
        doc = (TOOLS / "transient.py").read_text(encoding="utf-8")
        self.assertIn("429 er endelig", doc)


class ClassificationTests(unittest.TestCase):
    def test_a_status_classifies_by_contract(self) -> None:
        for status, expected in [
            (500, True), (502, True), (503, True), (599, True),
            (200, False), (301, False), (403, False), (404, False), (429, False),
        ]:
            with self.subTest(status=status):
                self.assertEqual(expected, transient.is_transient(status))
                self.assertEqual(expected, transient.is_transient(status, None))

    def test_a_network_failure_is_transient(self) -> None:
        for error in (RESET, "", "timed out"):
            with self.subTest(error=error):
                self.assertTrue(transient.is_transient(None, error))

    def test_a_response_wins_over_an_error_text(self) -> None:
        # `fetch` sætter aldrig begge, men funktionen er total, og et svar der
        # ignoreres ville kunne gøre en 429 forbigående igen. Kilden skal have
        # sagt 503, hvis den mente at der intet svar kom.
        self.assertFalse(transient.is_transient(429, RESET))
        self.assertFalse(transient.is_transient(404, RESET))
        self.assertTrue(transient.is_transient(503, RESET))

    def test_an_exception_classifies_by_contract(self) -> None:
        for error, expected in [
            (urllib.error.URLError("reset"), True),
            (TimeoutError("read operation timed out"), True),
            (ConnectionError("connection reset by peer"), True),
            (http_error(503), True),
            (http_error(429), False),
            (http_error(404), False),
            # Rå JSON der ikke parse er et ubrugeligt svar, ikke en fejl der
            # går over: et forsøg mere ville give samme svar.
            (ValueError("Expecting value"), False),
            (RuntimeError("ufuldstændige data"), False),
        ]:
            with self.subTest(error=type(error).__name__):
                self.assertEqual(expected, transient.is_transient(error=error))

    def test_an_http_error_is_a_response_not_a_network_error(self) -> None:
        # `HTTPError` arver fra `URLError`. Dømmer man den som netværksfejl bliver
        # alle 4xx forbigående, og så er 429-reglen ovenfor død kode.
        self.assertTrue(issubclass(urllib.error.HTTPError, urllib.error.URLError))
        self.assertFalse(transient.is_transient(error=http_error(403)))

    def test_both_forms_agree(self) -> None:
        # Den egentlige fejlform fra opgaven: to former for det samme svar.
        for code in (200, 403, 404, 429, 500, 503):
            with self.subTest(code=code):
                self.assertEqual(
                    transient.is_transient(error=http_error(code)),
                    transient.is_transient(code),
                )


class _FakeResponse:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class WeeklyReportRetryTests(unittest.TestCase):
    """`http_json` skal prøve en 5xx igen og en 429 ikke — målt i kaldeantal."""

    def calls_for(self, side_effect) -> int:
        with patch.object(report.urllib.request, "urlopen", side_effect=side_effect) as urlopen:
            with self.assertRaises(Exception):
                report.http_json("https://x/api/stats", timeout=5)
        return urlopen.call_count

    def test_a_server_error_is_retried(self) -> None:
        self.assertEqual(2, self.calls_for(http_error(503)))

    def test_a_rate_limit_is_not_retried(self) -> None:
        # Før opgaven var dette 2. Det er hele striden: et forsøg mere på en
        # 429 læser intet ind og trækker bare kvoten for den der spørger.
        self.assertEqual(1, self.calls_for(http_error(429)))

    def test_a_client_error_is_not_retried(self) -> None:
        self.assertEqual(1, self.calls_for(http_error(403)))

    def test_a_network_error_is_still_retried(self) -> None:
        # Uge 39 tabte hele trafikblokken på ét read-timeout. Den beskyttelse
        # må ikke forsvinde med 429-reglen.
        self.assertEqual(2, self.calls_for(TimeoutError("The read operation timed out")))

    def test_a_broken_payload_is_not_retried(self) -> None:
        self.assertEqual(1, self.calls_for(ValueError("Expecting value")))

    def test_a_recovered_server_error_still_yields_data(self) -> None:
        with patch.object(
            report.urllib.request, "urlopen",
            side_effect=[http_error(502), _FakeResponse(b'{"ok": true}')],
        ) as urlopen:
            self.assertEqual({"ok": True}, report.http_json("https://x/api/stats"))
        self.assertEqual(2, urlopen.call_count)


class SitemapPortRetryTests(unittest.TestCase):
    """Samme to svar, målt gennem `fetch_resilient` i stedet for `http_json`."""

    def setUp(self) -> None:
        self.calls = 0
        self.script: list = []
        self._sleep = check_live_sitemaps.time.sleep
        check_live_sitemaps.time.sleep = lambda _seconds: None
        self.addCleanup(setattr, check_live_sitemaps.time, "sleep", self._sleep)

    def _fetch(self, *_args, **_kwargs):
        self.calls += 1
        return self.script[min(self.calls - 1, len(self.script) - 1)]

    def run_fetch(self, script: list) -> tuple[int | None, str | None]:
        self.calls = 0
        self.script = script
        with patch.object(check_live_sitemaps, "fetch", side_effect=self._fetch):
            status, _body, _headers, error = check_live_sitemaps.fetch_resilient("https://mahope.tools/")
        return status, error

    def test_a_rate_limit_is_not_retried(self) -> None:
        self.assertEqual((429, None), self.run_fetch([(429, b"", None, None)]))

    def test_a_server_error_is_retried(self) -> None:
        self.run_fetch([(503, b"", None, None)])
        self.assertEqual(3, self.calls)

    def test_a_network_reset_is_retried(self) -> None:
        self.assertEqual((None, RESET), self.run_fetch([(None, b"", None, RESET)] * 5))
        self.assertEqual(3, self.calls)


if __name__ == "__main__":
    unittest.main(verbosity=2)
