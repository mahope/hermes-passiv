#!/usr/bin/env python3
from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import weekly_report as report


class ReportFixture:
    def setUp(self) -> None:
        report.ERRORS.clear()
        self.day = datetime.now(timezone.utc).date().isoformat()
        environment = patch.dict(os.environ, {"RESEND_API_KEY": "re_test_stats"})
        environment.start()
        self.addCleanup(environment.stop)

    def payload(self, *, empty: bool = False, sales_status: str = "ok") -> dict:
        domains = {}
        for index, domain in enumerate(report.TRAFFIC_DOMAINS):
            if empty:
                domains[domain] = {}
            else:
                path = f"/product-{index + 1}"
                domains[domain] = {self.day: {path: {"visits": index + 1, "uniques": 1}}}
        sales = {
            "scope": "all_time_gross_fulfillments",
            "by_product": {} if empty else {"clean-copy-pro": 3, "page-profile-pro": 2},
            "product_names": {} if empty else {
                "clean-copy-pro": "Clean Copy Pro",
                "page-profile-pro": "Page Profile Pro",
            },
        }
        return {
            "ok": True,
            "traffic_status": "ok",
            "unique_status": "ok",
            "domain_status": {domain: "ok" for domain in report.TRAFFIC_DOMAINS},
            "sales_status": sales_status,
            "stats_by_domain": domains,
            "downloads_by_domain": {domain: {} for domain in report.TRAFFIC_DOMAINS},
            "sales": sales if sales_status == "ok" else None,
            "waitlist": 0,
            "licenses_issued": 0 if empty else 5,
            "ai_asks": 0,
            "scans": 0,
        }

    def other_data(self, traffic: dict) -> dict:
        return {
            "schema_version": 2,
            "iso_week": "2026-39",
            "generated_at": "2026-09-25T12:00:00+00:00",
            "health": {},
            "traffic": traffic,
            "npm": {},
            "github": {},
            "bugreports": {"available": False, "note": "ikke testet"},
            "uptime": {},
            "links": {"available": False, "note": "ikke testet"},
            "errors": [],
        }


class WeeklyReportTests(ReportFixture, unittest.TestCase):
    def test_collects_all_domains_and_stripe_sales(self) -> None:
        with patch.object(report, "http_json", return_value=self.payload()):
            result = report.collect_stats(7)
        self.assertEqual("ok", result["status"])
        self.assertEqual(set(report.TRAFFIC_DOMAINS), set(result["domains"]))
        for domain in report.TRAFFIC_DOMAINS:
            self.assertEqual("ok", result["domains"][domain]["status"])
            self.assertTrue(result["domains"][domain]["top_paths"])
        self.assertEqual(10, result["visits"])
        self.assertEqual(3, result["sales"]["by_product"]["clean-copy-pro"])
        self.assertEqual(2, result["sales"]["by_product"]["page-profile-pro"])
        self.assertEqual("all_time_gross_fulfillments", result["sales"]["scope"])

    def test_stats_uses_server_side_bearer_authentication(self) -> None:
        with patch.object(report, "http_json", return_value=self.payload()) as http_json:
            result = report.collect_stats(7)
        args, kwargs = http_json.call_args
        self.assertEqual("ok", result["status"])
        # Rankingen gælder de seneste syv *fulde* dage, og API'ets `days`
        # tæller i dag med, så der hentes én dag mere end vinduet.
        self.assertEqual(f"https://mahope.tools/api/stats?days={report.RANKING_FETCH_DAYS}", args[0])
        self.assertNotIn("token=", args[0])
        self.assertEqual(f"Bearer {report.stats_bearer_token()}", kwargs["headers"]["Authorization"])

    def test_complete_empty_traffic_does_not_invent_sales(self) -> None:
        with patch.object(report, "http_json", return_value=self.payload(empty=True, sales_status="unknown")):
            result = report.collect_stats(7)
        self.assertEqual("unknown", result["status"])
        self.assertIsNone(result["visits"])
        self.assertEqual("unknown", result["sales"]["status"])
        self.assertNotIn("by_product", result["sales"])
        self.assertIsNone(result["licenses_issued"])
        self.assertTrue(all(result["domains"][domain]["status"] == "unknown" for domain in report.TRAFFIC_DOMAINS))

    def test_missing_sales_is_unknown(self) -> None:
        with patch.object(report, "http_json", return_value=self.payload(sales_status="unknown")):
            result = report.collect_stats(7)
        self.assertEqual("ok", result["status"])
        self.assertEqual("unknown", result["sales"]["status"])
        self.assertNotIn("by_product", result["sales"])

    def test_missing_visit_value_is_not_coerced_to_zero(self) -> None:
        payload = self.payload()
        payload["stats_by_domain"]["mahope.tools"][self.day]["/product-4"]["visits"] = None
        with patch.object(report, "http_json", return_value=payload):
            result = report.collect_stats(7)
        self.assertEqual("unknown", result["status"])
        self.assertIsNone(result["visits"])
        self.assertTrue(result["error"])

    def test_missing_unique_value_keeps_pageviews_without_inventing_uniques(self) -> None:
        payload = self.payload()
        payload["unique_status"] = "unknown"
        payload["stats_by_domain"]["mahope.tools"][self.day]["/product-4"]["uniques"] = None
        with patch.object(report, "http_json", return_value=payload):
            result = report.collect_stats(7)
        self.assertEqual("ok", result["status"])
        self.assertEqual("unknown", result["unique_status"])
        self.assertEqual(10, result["visits"])

    def test_unknown_traffic_preserves_known_sales(self) -> None:
        payload = self.payload()
        payload["traffic_status"] = "unknown"
        payload["domain_status"] = {domain: "unknown" for domain in report.TRAFFIC_DOMAINS}
        payload["stats_by_domain"] = {domain: None for domain in report.TRAFFIC_DOMAINS}
        payload["downloads_by_domain"] = {domain: None for domain in report.TRAFFIC_DOMAINS}
        with patch.object(report, "http_json", return_value=payload):
            result = report.collect_stats(7)
        self.assertEqual("unknown", result["status"])
        self.assertIsNone(result["visits"])
        self.assertEqual(3, result["sales"]["by_product"]["clean-copy-pro"])

    def test_uninstrumented_domain_stays_unknown(self) -> None:
        payload = self.payload()
        payload["traffic_status"] = "partial"
        payload["domain_status"]["bugbottle.dev"] = "unknown"
        payload["stats_by_domain"]["bugbottle.dev"] = None
        payload["downloads_by_domain"]["bugbottle.dev"] = None
        with patch.object(report, "http_json", return_value=payload):
            result = report.collect_stats(7)
        self.assertEqual("partial", result["status"])
        self.assertIsNone(result["visits"])
        self.assertEqual("unknown", result["domains"]["bugbottle.dev"]["status"])
        self.assertEqual("ok", result["domains"]["cleancopy.tools"]["status"])

    def test_partial_payload_without_known_domains_is_unknown(self) -> None:
        payload = self.payload()
        payload["traffic_status"] = "partial"
        payload["domain_status"] = {domain: "unknown" for domain in report.TRAFFIC_DOMAINS}
        payload["stats_by_domain"] = {domain: None for domain in report.TRAFFIC_DOMAINS}
        payload["downloads_by_domain"] = {domain: None for domain in report.TRAFFIC_DOMAINS}
        with patch.object(report, "http_json", return_value=payload):
            result = report.collect_stats(7)
        self.assertEqual("unknown", result["status"])
        self.assertIsNone(result["visits"])
        self.assertTrue(all(result["domains"][domain]["status"] == "unknown" for domain in report.TRAFFIC_DOMAINS))
        self.assertTrue(all(result["download_domains"][domain]["status"] == "unknown" for domain in report.TRAFFIC_DOMAINS))

    def test_health_unknown_traffic_is_not_reported_as_zero(self) -> None:
        with patch.object(report, "http_json", return_value={
            "status": "healthy",
            "kv": True,
            "traffic_status": "unknown",
            "stats": {"recentVisits": 0, "recentDownloads": 0, "waitlist": 0, "scans": 0},
        }):
            result = report.collect_health()
        self.assertEqual("unknown", result["traffic_status"])
        self.assertIsNone(result["visits_2d"])
        self.assertIsNone(result["downloads_2d"])
        self.assertEqual(0, result["waitlist"])

    def test_health_partial_traffic_keeps_known_counts(self) -> None:
        with patch.object(report, "http_json", return_value={
            "status": "healthy",
            "kv": True,
            "traffic_status": "partial",
            "stats": {"recentVisits": 12, "recentDownloads": 3, "waitlist": 0, "scans": 0},
        }):
            result = report.collect_health()
        self.assertEqual("partial", result["traffic_status"])
        self.assertEqual(12, result["visits_2d"])
        self.assertEqual(3, result["downloads_2d"])

    def test_legacy_schema_does_not_create_false_traffic_delta(self) -> None:
        with patch.object(report, "http_json", return_value=self.payload()):
            traffic = report.collect_stats(7)
        data = self.other_data(traffic)
        previous = {"iso_week": "2026-38", "traffic": {"visits": 706, "downloads": 340}}
        subject, notable, sections = report.build_report(data, previous)
        markdown = report.render_markdown(data, previous, notable, sections)
        self.assertIn("| Besøg (7 dage) | 10 | — |", markdown)

    def test_invalid_counters_are_unknown(self) -> None:
        payload = self.payload()
        payload["waitlist"] = "many"
        payload["licenses_issued"] = []
        payload["ai_asks"] = {}
        payload["scans"] = "0"
        with patch.object(report, "http_json", return_value=payload):
            result = report.collect_stats(7)
        self.assertIsNone(result["waitlist"])
        self.assertIsNone(result["licenses_issued"])
        self.assertIsNone(result["ai_asks"])
        self.assertIsNone(result["scans"])

    def test_timeout_is_explicitly_unknown(self) -> None:
        collectors = {
            "collect_health": {"status": "healthy", "kv": True, "stats": {}},
            "collect_npm": {},
            "collect_github": {},
            "collect_bugreports": {"available": False, "note": "ikke testet"},
            "collect_uptime": {},
            "collect_links": {"available": False, "note": "ikke testet"},
        }
        with patch.object(report, "collect_stats", side_effect=TimeoutError("timeout")), \
                patch.object(report, "collect_health", return_value=collectors["collect_health"]), \
                patch.object(report, "collect_npm", return_value=collectors["collect_npm"]), \
                patch.object(report, "collect_github", return_value=collectors["collect_github"]), \
                patch.object(report, "collect_bugreports", return_value=collectors["collect_bugreports"]), \
                patch.object(report, "collect_uptime", return_value=collectors["collect_uptime"]), \
                patch.object(report, "collect_links", return_value=collectors["collect_links"]):
            data = report.collect_all()
        self.assertFalse(data["traffic"]["available"])
        self.assertEqual("unknown", data["traffic"]["status"])
        self.assertIsNone(data["traffic"]["visits"])
        self.assertEqual(set(report.TRAFFIC_DOMAINS), set(data["traffic"]["domains"]))
        subject, notable, sections = report.build_report(data, None)
        markdown = report.render_markdown(data, None, notable, sections)
        self.assertIn("ukendt", subject.lower() + markdown.lower())
        self.assertNotIn("Besøg (7 dage) | 0 |", markdown)

    def test_report_renders_each_domain_and_sales(self) -> None:
        with patch.object(report, "http_json", return_value=self.payload()):
            traffic = report.collect_stats(7)
        data = self.other_data(traffic)
        subject, notable, sections = report.build_report(data, None)
        titles = [section["title"] for section in sections]
        for domain in report.TRAFFIC_DOMAINS:
            self.assertTrue(any(domain in title for title in titles), titles)
        self.assertTrue(any("Stripe-salg" in title for title in titles), titles)
        markdown = report.render_markdown(data, None, notable, sections)
        self.assertIn("alle tider", markdown)
        self.assertIn("Clean Copy Pro", markdown)
        self.assertIn("Page Profile Pro", markdown)


class RankingTests(ReportFixture, unittest.TestCase):
    """Rangeringen må aldrig påstå en mest-besøgt-liste uden datagrundlag."""

    def ranked_payload(self, *, per_domain: dict, days: tuple[str, ...] | None = None) -> dict:
        """Payload med trafik spredt over de seneste fulde dage.

        Tallene i `per_domain` er domænets samlede pageviews i rankingvinduet
        og skrives på vindets sidste dag, så både periodens total og
        syvdagesoversigten bliver præcis summen.
        """
        start, end = report.ranking_period()
        window = list(days or [start, end])
        domains = {}
        for domain in report.TRAFFIC_DOMAINS:
            paths = per_domain.get(domain) or {}
            domains[domain] = {
                day: ({path: {"visits": visits, "uniques": visits} for path, visits in paths.items()}
                      if day == window[-1] else {})
                for day in window
            }
        payload = self.payload()
        payload["stats_by_domain"] = domains
        return payload

    def test_ranking_period_is_seven_full_days_without_today(self) -> None:
        today = datetime.now(timezone.utc).date()
        start, end = report.ranking_period(today=today)
        self.assertEqual((today - report.timedelta(days=7)).isoformat(), start)
        self.assertEqual((today - report.timedelta(days=1)).isoformat(), end)
        self.assertLess(start, end)
        self.assertNotIn(today.isoformat(), (start, end))

    def test_traffic_basis_ranks_offer_pages_by_domain_and_route(self) -> None:
        start, end = report.ranking_period()
        payload = self.ranked_payload(per_domain={
            "mahope.tools": {"/page-profile": 9, "/": 20, "/scan": 4},
            "cleancopy.tools": {"/": 11},
            "deskuptime.com": {"/": 7},
            "bugbottle.dev": {"/": 6},
        })
        with patch.object(report, "http_json", return_value=payload):
            ranking = report.collect_stats(7)["ranking"]
        self.assertEqual("traffic", ranking["basis"])
        self.assertIsNone(ranking["basis_reason"])
        self.assertEqual(57, ranking["total_pageviews"])
        self.assertEqual(["mahope.tools", "cleancopy.tools", "deskuptime.com", "bugbottle.dev"],
                         [row["domain"] for row in ranking["ranked_domains"]])
        ranked = {(row["domain"], row["route"]): row["visits"] for row in ranking["ranked_offer_pages"]}
        self.assertEqual(9, ranked[("mahope.tools", "/page-profile")])
        self.assertEqual(11, ranked[("cleancopy.tools", "/")])
        self.assertEqual(7, ranked[("deskuptime.com", "/")])
        self.assertEqual(4, ranked[("mahope.tools", "/scan")])
        # mahope.tools' forside sælger intet direkte og er derfor ikke med.
        self.assertEqual([11, 9, 7, 4], [row["visits"] for row in ranking["ranked_offer_pages"]])
        self.assertIsNone(ranking["fallback"])
        self.assertEqual({"days": 7, "kind": "last_7_full_days", "start": start, "end": end},
                         ranking["period"])

    def test_todays_partial_traffic_never_enters_the_ranking(self) -> None:
        today = datetime.now(timezone.utc).date().isoformat()
        start, end = report.ranking_period()
        payload = self.ranked_payload(per_domain={
            "mahope.tools": {"/page-profile": 12},
            "cleancopy.tools": {"/": 12},
            "deskuptime.com": {"/": 12},
            "bugbottle.dev": {"/": 12},
        })
        # 500 besøg i dag må hverken give basis `traffic` med et oppblæst tal
        # eller fortrænge de syv fulde dage.
        payload["stats_by_domain"]["mahope.tools"][today] = {"/page-profile": {"visits": 500, "uniques": 500}}
        with patch.object(report, "http_json", return_value=payload):
            ranking = report.collect_stats(7)["ranking"]
        self.assertEqual("traffic", ranking["basis"])
        self.assertEqual(48, ranking["total_pageviews"])
        ranked = {(row["domain"], row["route"]): row["visits"] for row in ranking["ranked_offer_pages"]}
        self.assertEqual(12, ranked[("mahope.tools", "/page-profile")])
        self.assertNotIn(today, (ranking["period"]["start"], ranking["period"]["end"]))
        self.assertNotIn(today, (start, end))

    def test_fewer_than_thirty_pageviews_is_unknown_with_documented_fallback(self) -> None:
        payload = self.ranked_payload(per_domain={
            "mahope.tools": {"/page-profile": 9},
            "cleancopy.tools": {"/": 9},
            "deskuptime.com": {"/": 9},
            "bugbottle.dev": {"/": 2},
        })
        with patch.object(report, "http_json", return_value=payload):
            ranking = report.collect_stats(7)["ranking"]
        self.assertEqual("unknown", ranking["basis"])
        self.assertIn("29", ranking["basis_reason"])
        self.assertEqual([], ranking["ranked_offer_pages"])
        fallback = ranking["fallback"]
        self.assertFalse(fallback["is_traffic_ranking"])
        self.assertEqual(4, len(fallback["core_pages"]))
        self.assertEqual(
            ["cleancopy.tools", "deskuptime.com", "mahope.tools", "mahope.tools"],
            [page["domain"] for page in fallback["core_pages"]],
        )
        self.assertTrue(all(page["why"] for page in fallback["core_pages"]))
        self.assertTrue(any(page["product"] == "clean-copy-pro" for page in fallback["core_pages"]))
        self.assertGreaterEqual(len(fallback["offer_pages"]), 10)

    def test_domain_below_five_pageviews_is_never_ranked(self) -> None:
        payload = self.ranked_payload(per_domain={
            "mahope.tools": {"/page-profile": 40},
            "cleancopy.tools": {"/": 20},
            "deskuptime.com": {"/": 4},
            "bugbottle.dev": {"/": 6},
        })
        with patch.object(report, "http_json", return_value=payload):
            ranking = report.collect_stats(7)["ranking"]
        self.assertEqual("traffic", ranking["basis"])
        # bugbottle.dev har 6 og rangeres med; deskuptime.com har 4 og gør ikke.
        self.assertEqual(["mahope.tools", "cleancopy.tools", "bugbottle.dev"],
                         [row["domain"] for row in ranking["ranked_domains"]])
        below = {row["domain"]: row for row in ranking["domains_below_threshold"]}
        self.assertEqual(4, below["deskuptime.com"]["visits"])
        self.assertIn("5", below["deskuptime.com"]["reason"])

    def test_no_domain_above_the_floor_is_unknown(self) -> None:
        payload = self.ranked_payload(per_domain={
            "mahope.tools": {"/page-profile": 4},
            "cleancopy.tools": {"/": 4},
            "deskuptime.com": {"/": 4},
            "bugbottle.dev": {"/": 4},
        })
        with patch.object(report, "http_json", return_value=payload):
            ranking = report.collect_stats(7)["ranking"]
        self.assertEqual("unknown", ranking["basis"])
        self.assertIn("5 verificerede pageviews", ranking["basis_reason"])
        self.assertIsNotNone(ranking["fallback"])

    def test_uninstrumented_domain_blocks_the_ranking(self) -> None:
        payload = self.ranked_payload(per_domain={
            "mahope.tools": {"/page-profile": 200},
            "cleancopy.tools": {"/": 60},
            "deskuptime.com": {"/": 60},
        })
        with patch.object(report, "http_json", return_value=payload):
            ranking = report.collect_stats(7)["ranking"]
        self.assertEqual("unknown", ranking["basis"])
        self.assertIn("bugbottle.dev", ranking["basis_reason"])
        self.assertEqual([], ranking["ranked_domains"])
        self.assertIsNotNone(ranking["fallback"])

    def test_missing_inventory_makes_the_fallback_unknown_instead_of_empty(self) -> None:
        with patch.object(report, "load_offer_inventory", return_value=None):
            payload = self.ranked_payload(per_domain={
                "mahope.tools": {"/page-profile": 12},
                "cleancopy.tools": {"/": 12},
                "deskuptime.com": {"/": 12},
                "bugbottle.dev": {"/": 12},
            })
            with patch.object(report, "http_json", return_value=payload):
                ranking = report.collect_stats(7)["ranking"]
            with patch.object(report, "http_json", return_value=self.payload(empty=True)):
                failed = report.collect_stats(7)["ranking"]
        # Uden inventar kan de sælgende sider ikke identificeres, så selv
        # verificeret trafik må ikke give en rangering.
        self.assertEqual("unknown", ranking["basis"])
        self.assertIn("købsinventaret", ranking["basis_reason"])
        self.assertEqual([], ranking["ranked_offer_pages"])
        self.assertIsNone(ranking["fallback"])
        self.assertEqual("unknown", failed["basis"])
        self.assertIsNone(failed["fallback"])

    def test_unknown_traffic_reports_unknown_ranking_with_fallback(self) -> None:
        payload = self.payload()
        payload["traffic_status"] = "unknown"
        payload["domain_status"] = {domain: "unknown" for domain in report.TRAFFIC_DOMAINS}
        payload["stats_by_domain"] = {domain: None for domain in report.TRAFFIC_DOMAINS}
        payload["downloads_by_domain"] = {domain: None for domain in report.TRAFFIC_DOMAINS}
        with patch.object(report, "http_json", return_value=payload):
            result = report.collect_stats(7)
        ranking = result["ranking"]
        self.assertEqual("unknown", ranking["basis"])
        self.assertIsNone(ranking["total_pageviews"])
        self.assertEqual([], ranking["ranked_domains"])
        self.assertEqual(4, len(ranking["fallback"]["core_pages"]))

    def test_collect_all_exposes_top_level_ranking_basis(self) -> None:
        with patch.object(report, "http_json", return_value=self.ranked_payload(per_domain={
                "mahope.tools": {"/page-profile": 9}, "cleancopy.tools": {"/": 9}, "deskuptime.com": {"/": 9}})):
            with patch.object(report, "collect_health", return_value={"status": "healthy", "kv": True, "stats": {}}), \
                 patch.object(report, "collect_npm", return_value={}), \
                 patch.object(report, "collect_github", return_value={}), \
                 patch.object(report, "collect_bugreports", return_value={"available": False}), \
                 patch.object(report, "collect_uptime", return_value={}), \
                 patch.object(report, "collect_links", return_value={"available": False}):
                data = report.collect_all()
        self.assertEqual("unknown", data["ranking_basis"])

    def test_report_renders_ranking_basis_and_fallback_without_claiming_visits(self) -> None:
        payload = self.ranked_payload(per_domain={
            "mahope.tools": {"/page-profile": 9},
            "cleancopy.tools": {"/": 9},
            "deskuptime.com": {"/": 8},
            "bugbottle.dev": {"/": 2},
        })
        with patch.object(report, "http_json", return_value=payload):
            traffic = report.collect_stats(7)
        data = self.other_data(traffic)
        subject, notable, sections = report.build_report(data, None)
        markdown = report.render_markdown(data, None, notable, sections)
        self.assertIn("ranking_basis: **unknown**", markdown)
        self.assertIn("Konverteringsrangering", markdown)
        self.assertIn("ikke** en mest-besøgte-rangering", markdown)
        self.assertIn("cleancopy.tools/", markdown)
        self.assertIn("mahope.tools/page-profile", markdown)
        self.assertIn("Synlige Pro-tilbud", markdown)
        self.assertIn("ikke en rangering efter besøg", markdown)
        titles = [section["title"] for section in sections]
        self.assertTrue(any("Stripe-salg" in title for title in titles), titles)

    def test_ranked_report_lists_offer_pages_with_real_visits(self) -> None:
        payload = self.ranked_payload(per_domain={
            "mahope.tools": {"/page-profile": 9, "/scan": 2},
            "cleancopy.tools": {"/": 20},
            "deskuptime.com": {"/": 7},
            "bugbottle.dev": {"/": 6},
        })
        with patch.object(report, "http_json", return_value=payload):
            traffic = report.collect_stats(7)
        data = self.other_data(traffic)
        subject, notable, sections = report.build_report(data, None)
        markdown = report.render_markdown(data, None, notable, sections)
        self.assertEqual("traffic", traffic["ranking"]["basis"])
        self.assertIn("ranking_basis: **traffic**", markdown)
        self.assertIn("| mahope.tools/page-profile | page-profile-pro | 9 |", markdown)
        self.assertIn("| cleancopy.tools/ | clean-copy-pro | 20 |", markdown)
        self.assertNotIn("Synlige Pro-tilbud", markdown)

    def test_thresholds_are_the_documented_contract_values(self) -> None:
        self.assertEqual(7, report.RANKING_DAYS)
        self.assertEqual(30, report.RANKING_MIN_TOTAL_PAGEVIEWS)
        self.assertEqual(5, report.RANKING_MIN_PAGEVIEWS_PER_DOMAIN)
        self.assertEqual(8, report.RANKING_FETCH_DAYS)


if __name__ == "__main__":
    unittest.main()
