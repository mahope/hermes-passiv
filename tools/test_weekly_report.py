#!/usr/bin/env python3
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import weekly_report as report


class WeeklyReportTests(unittest.TestCase):
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
        self.assertEqual("https://mahope.tools/api/stats?days=7", args[0])
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


if __name__ == "__main__":
    unittest.main()
