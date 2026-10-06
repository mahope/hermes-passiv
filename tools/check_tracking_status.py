#!/usr/bin/env python3
"""Check if zero windowed data means no visitors or tracking broken.

This tool helps distinguish between "ingen besøgende" (no visitors) and
"tracking død" (tracking broken) by comparing windowed data from
/api/results and /api/conversion with recent visitor data from /api/health.

Usage:
    python3 tools/check_tracking_status.py
    python3 tools/check_tracking_status.py --help
"""

import json
import sys
import argparse
import urllib.error
import urllib.request
from datetime import datetime, timezone


SITE = "https://mahope.tools"


def http_json(url: str, timeout: int = 30):
    """Fetch JSON from URL with basic error handling."""
    req = urllib.request.Request(url, headers={"User-Agent": "mahope-tracking-status/1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"Error fetching {url}: {exc}", file=sys.stderr)
        return None


def check_tracking_status():
    """Check tracking status and return assessment."""
    # Fetch 7-day data from both endpoints
    results_data = http_json(f"{SITE}/api/results?days=7")
    conversion_data = http_json(f"{SITE}/api/conversion?days=7")
    health_data = http_json(f"{SITE}/api/health")
    
    if not all([results_data, conversion_data, health_data]):
        return "Error: Could not fetch required data"
    
    # Check if windowed data shows zero activity
    results_zero = (
        results_data.get("totals", {}).get("runs", 0) == 0 and
        results_data.get("totals", {}).get("visitor_days", 0) == 0
    )
    
    conversion_zero = (
        conversion_data.get("totals", {}).get("buy_clicks", 0) == 0 and
        conversion_data.get("totals", {}).get("pro_card_clicks", 0) == 0 and
        conversion_data.get("totals", {}).get("visitor_days", 0) == 0
    )
    
    # If either endpoint shows activity, tracking is working
    if not (results_zero and conversion_zero):
        # Format the actual values for reporting
        results_runs = results_data.get("totals", {}).get("runs", 0)
        results_visitor_days = results_data.get("totals", {}).get("visitor_days", 0)
        conversion_buy_clicks = conversion_data.get("totals", {}).get("buy_clicks", 0)
        conversion_pro_card_clicks = conversion_data.get("totals", {}).get("pro_card_clicks", 0)
        conversion_visitor_days = conversion_data.get("totals", {}).get("visitor_days", 0)
        
        return (
            f"Tracking appears to be working:\n"
            f"  /api/results (7 days): {results_runs} runs, {results_visitor_days} visitor_days\n"
            f"  /api/conversion (7 days): {conversion_buy_clicks} buy_clicks, "
            f"{conversion_pro_card_clicks} pro_card_clicks, {conversion_visitor_days} visitor_days"
        )
    
    # Both endpoints show zero activity - check if we can confirm it's really zero.
    # `recentVisits` lives under `stats` in /api/health (measured 6/10), not at the
    # top level, so reading it from the top level made this branch unreachable:
    # the tool could never say "tracking død" even on the day it was true.
    stats = health_data.get("stats") or {}
    recent_visits = int(stats.get("recentVisits") or 0)
    recent_downloads = int(stats.get("recentDownloads") or 0)
    recent_events = int(stats.get("recentEvents") or 0)
    scans_lifetime = int(stats.get("scans_lifetime") or 0)
    waitlist_lifetime = int(stats.get("waitlist_lifetime") or 0)

    if recent_visits > 0:
        return (
            "TRACKING DØD (the client-side counters are broken, not the traffic)\n"
            f"Reason: /api/health shows {recent_visits} visits and {recent_downloads} "
            f"downloads in the last 2 days,\n"
            f"and /api/health already counts {recent_events} recent events server-side,\n"
            "but /api/results and /api/conversion are both zero for 7 days.\n"
            "Visitors arrive, so a zero in those two lists means their events never\n"
            "landed. Every baseline taken from them is unconfirmed until this is fixed."
        )

    # No recent visits detected, but we can't be certain there are no visitors at all
    # (they might have visited more than 2 days ago but less than 28 days ago)
    return (
        "0 = ubekreftet (zero is unconfirmed)\n"
        f"Reason: No recent visits detected in /api/health (last 2 days: {recent_visits}),\n"
        f"but lifetime counters show activity (scans_lifetime: {scans_lifetime}, "
        f"waitlist_lifetime: {waitlist_lifetime}).\n"
        "This could mean either no visitors at all or tracking broken for recent visitors.\n"
        "Definitive assessment requires historical counter data to check if lifetime "
        "counters are increasing."
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version", 
        action="version",
        version="%(prog)s 1.0"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the two verdicts against fixed /api responses",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    result = check_tracking_status()
    print(result)


def _verdict(results, conversion, health):
    """The verdict, computed from three fixed responses. Split out so the
    self-test can drive it without a network call."""
    original = http_json
    payloads = {
        f"{SITE}/api/results?days=7": results,
        f"{SITE}/api/conversion?days=7": conversion,
        f"{SITE}/api/health": health,
    }
    try:
        globals()["http_json"] = lambda url, timeout=30: payloads.get(url)
        return check_tracking_status()
    finally:
        globals()["http_json"] = original


ZERO_RESULTS = {"totals": {"runs": 0, "visitor_days": 0}}
ZERO_CONVERSION = {"totals": {"buy_clicks": 0, "pro_card_clicks": 0, "visitor_days": 0}}


def self_test():
    """Both verdicts, on the shapes /api actually returns.

    The red case is the one measured live 6/10: 20 visits in two days and two
    zero windows. Before the fix it printed "No recent visits detected" while
    quoting 20, and never reached the broken verdict at all.
    """
    cases = [
        (
            "besøgende, nul tællere -> tracking død",
            ZERO_RESULTS,
            ZERO_CONVERSION,
            {"stats": {"recentVisits": 20, "recentDownloads": 55,
                       "recentEvents": 2, "scans_lifetime": 53, "waitlist_lifetime": 0}},
            ("TRACKING DØD", "20 visits"),
        ),
        (
            "ingen besøgende -> ubekreftet",
            ZERO_RESULTS,
            ZERO_CONVERSION,
            {"stats": {"recentVisits": 0, "recentDownloads": 0, "recentEvents": 0,
                       "scans_lifetime": 53, "waitlist_lifetime": 0}},
            ("0 = ubekreftet", "No recent visits"),
        ),
        (
            "et købsklik -> tracking virker",
            ZERO_RESULTS,
            {"totals": {"buy_clicks": 1, "pro_card_clicks": 0, "visitor_days": 1}},
            {"stats": {"recentVisits": 4}},
            ("Tracking appears to be working", "1 buy_clicks"),
        ),
    ]
    failed = 0
    for name, results, conversion, health, expected in cases:
        got = _verdict(results, conversion, health)
        missing = [part for part in expected if part not in got]
        if missing:
            failed += 1
            print(f"FAIL {name}: mangler {missing}\n{got}")
        else:
            print(f"OK   {name}")
    print(f"check_tracking_status --self-test: {len(cases) - failed}/{len(cases)}")
    return 1 if failed else 0


if __name__ == "__main__":
    main()