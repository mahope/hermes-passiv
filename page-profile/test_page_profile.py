#!/usr/bin/env python3
import importlib.util
import io
import json
import os
import tempfile
import time
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

MODULE_PATH = Path(__file__).with_name("page_profile.py")
ROOT = MODULE_PATH.parent.parent
SPEC = importlib.util.spec_from_file_location("page_profile", MODULE_PATH)
page_profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(page_profile)

VALID_KEY = "0123456789ABCDEF" * 2
SEVEN_DAYS = 7 * 24 * 60 * 60


def response(payload, status=200):
    return HTTPError("https://mahope.tools/", status, "error", {}, io.BytesIO(json.dumps(payload).encode()))


def success(payload):
    return io.BytesIO(json.dumps(payload).encode())


class PageProfileLicenseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.license_file = Path(self.temp.name) / ".page-profile-license"
        self.environment = patch.dict(os.environ, {"PAGE_PROFILE_LICENSE": ""})
        self.environment.start()
        self.license_path = patch.object(page_profile, "LICENSE_FILE", str(self.license_file))
        self.license_path.start()
        self.addCleanup(self.environment.stop)
        self.addCleanup(self.license_path.stop)
        self.addCleanup(self.temp.cleanup)

    def write_state(self, *, validated_at, key=VALID_KEY.lower(), device_id="device-1"):
        self.license_file.write_text(
            json.dumps({
                "license_key": key,
                "device_id": device_id,
                "validated_at": validated_at,
            }),
            encoding="utf-8",
        )

    def test_activation_accepts_and_normalizes_a_stripe_key(self):
        payload = {
            "ok": True,
            "activated": True,
            "plan": "pro-yearly",
            "expires_at": "2027-09-25T00:00:00Z",
            "devices_in_use": 1,
        }
        with patch.object(page_profile, "urlopen", return_value=success(payload)) as urlopen:
            page_profile.activate(f"  {VALID_KEY}  ")

        request = urlopen.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual("https://mahope.tools/api/license/activate", request.full_url)
        self.assertEqual(VALID_KEY.lower(), body["license_key"])
        self.assertEqual("page-profile-pro", body["product"])
        self.assertTrue(body["device_id"])
        self.assertLessEqual(len(body["device_id"]), 128)
        state = json.loads(self.license_file.read_text(encoding="utf-8"))
        self.assertEqual(VALID_KEY.lower(), state["license_key"])
        self.assertEqual(body["device_id"], state["device_id"])
        self.assertIsInstance(state["validated_at"], (int, float))
        self.assertEqual(0o600, self.license_file.stat().st_mode & 0o777)

    def test_validation_uses_the_stored_device_and_updates_the_cache(self):
        now = 1_800_000_000
        self.write_state(validated_at=now - 100)
        payload = {"ok": True, "valid": True, "plan": "pro-yearly", "expires_at": None}
        with patch.object(page_profile.time, "time", return_value=now), patch.object(
            page_profile, "urlopen", return_value=success(payload)
        ) as urlopen:
            self.assertEqual(VALID_KEY.lower(), page_profile.require_pro("batch mode"))

        request = urlopen.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual("https://mahope.tools/api/license/validate", request.full_url)
        self.assertEqual("device-1", body["device_id"])
        self.assertEqual(now, json.loads(self.license_file.read_text(encoding="utf-8"))["validated_at"])

    def test_network_failure_uses_a_fresh_positive_cache(self):
        now = 1_800_000_000
        self.write_state(validated_at=now - SEVEN_DAYS + 1)
        with patch.object(page_profile.time, "time", return_value=now), patch.object(
            page_profile, "urlopen", side_effect=URLError("offline")
        ):
            self.assertEqual(VALID_KEY.lower(), page_profile.require_pro("batch mode"))

    def test_any_5xx_uses_a_fresh_positive_cache(self):
        now = 1_800_000_000
        for status in (500, 502, 503):
            with self.subTest(status=status):
                self.write_state(validated_at=now - SEVEN_DAYS + 1)
                failure = response({"ok": False, "error": "Service temporarily unavailable."}, status)
                with patch.object(page_profile.time, "time", return_value=now), patch.object(
                    page_profile, "urlopen", side_effect=failure
                ):
                    self.assertEqual(VALID_KEY.lower(), page_profile.require_pro("batch mode"))

    def test_service_failure_does_not_use_a_cache_older_than_seven_days(self):
        now = 1_800_000_000
        self.write_state(validated_at=now - SEVEN_DAYS - 1)
        failure = response({"ok": False, "error": "Service temporarily unavailable."}, 503)
        with patch.object(page_profile.time, "time", return_value=now), patch.object(
            page_profile, "urlopen", side_effect=failure
        ), redirect_stderr(io.StringIO()) as stderr, self.assertRaises(SystemExit) as raised:
            page_profile.require_pro("batch mode")
        self.assertEqual(2, raised.exception.code)
        self.assertIn("temporarily unavailable", stderr.getvalue().lower())

    def test_hard_failures_never_use_the_positive_cache(self):
        cases = {
            403: "revoked",
            404: "not found",
            409: "device limit",
        }
        now = 1_800_000_000
        for status, expected in cases.items():
            with self.subTest(status=status), patch.object(page_profile.time, "time", return_value=now):
                self.write_state(validated_at=now - 10)
                failure = response({"ok": False, "error": f"License {expected}"}, status)
                with patch.object(page_profile, "urlopen", side_effect=failure), redirect_stderr(
                    io.StringIO()
                ) as stderr, self.assertRaises(SystemExit) as raised:
                    page_profile.require_pro("batch mode")
                self.assertEqual(2, raised.exception.code)
                self.assertIn(expected, stderr.getvalue().lower())

    def test_malformed_success_response_never_uses_the_positive_cache(self):
        self.write_state(validated_at=time.time())
        with patch.object(page_profile, "urlopen", return_value=io.BytesIO(b"not-json")), redirect_stderr(
            io.StringIO()
        ) as stderr, self.assertRaises(SystemExit):
            page_profile.require_pro("batch mode")
        self.assertIn("invalid response", stderr.getvalue().lower())

    def test_invalid_validation_response_is_a_hard_failure(self):
        self.write_state(validated_at=time.time())
        payload = {"ok": True, "valid": False, "reason": "not_activated", "devices_in_use": 0}
        with patch.object(page_profile, "urlopen", return_value=success(payload)), redirect_stderr(
            io.StringIO()
        ) as stderr, self.assertRaises(SystemExit):
            page_profile.require_pro("batch mode")
        self.assertIn("activate", stderr.getvalue().lower())

    def test_activation_is_not_stored_when_the_service_is_unavailable(self):
        failure = response({"ok": False, "error": "Service temporarily unavailable."}, 503)
        with patch.object(page_profile, "urlopen", side_effect=failure), redirect_stderr(
            io.StringIO()
        ) as stderr, self.assertRaises(SystemExit):
            page_profile.activate(VALID_KEY)
        self.assertFalse(self.license_file.exists())
        self.assertIn("temporarily unavailable", stderr.getvalue().lower())

    def test_public_page_profile_claims_match_online_licensing(self):
        sources = (
            "site/page-profile.html",
            "site/da/page-profile.html",
            "site/da/blog/tjek-hastighed-uden-lighthouse.html",
            "tools/make_blog_da_mirrors_460.py",
        )
        forbidden = (
            "keys work offline",
            "offline license",
            "offline licens",
            "no phoning home",
            "offline licensnøgler",
            "offline-capable",
        )
        for relative in sources:
            with self.subTest(source=relative):
                text = (ROOT / relative).read_text(encoding="utf-8").casefold()
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)
                self.assertIn("mahope.tools", text)
                self.assertTrue("seven days" in text or "syv dage" in text)

    def test_legacy_key_format_and_generator_are_removed(self):
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("PPRO-", source)
        self.assertNotIn("--gen-key", source)
        self.assertNotIn("make_license_key", source)
        with self.assertRaises(ValueError):
            page_profile.normalize_license_key("PPRO-" + "A" * 32)


if __name__ == "__main__":
    unittest.main()
