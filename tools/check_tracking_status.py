#!/usr/bin/env python3
"""Check if zero windowed data means no visitors or tracking broken.

This tool helps distinguish between "ingen besøgende" (no visitors) and
"tracking død" (tracking broken) by comparing windowed data from
/api/results and /api/conversion with recent visitor data from /api/health.

The decisive number is `recentEvents`: /api/health and /api/results read the
same `p:v3:…:event:…` keys, so a non-zero `recentEvents` *proves* the client
write path works. Before 6/10 the tool said "TRACKING DØD" while quoting a
non-zero `recentEvents` in the same sentence.

Usage:
    python3 tools/check_tracking_status.py
    python3 tools/check_tracking_status.py --self-test
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

    # Målt 6/10: en hændelse skrevet med `fetch` til `/api/track` var synlig i
    # `/api/health` **33 sekunder** senere. KV-listninger er asynkrone, så et
    # nul lagt lige efter en udrulning er et nul *endnu* — ikke et dødt spor.
    LAG_NOTE = (
        "Note: Cloudflare KV listings are asynchronous. Measured 6/10: a fresh\n"
        "/api/track write became visible 33 seconds later, so a zero read right\n"
        "after a deploy is not evidence of a dead pipeline."
    )

    # `recentEvents` og `/api/results` læser **samme nøgler**. `handleTrack`
    # skriver dem gennem ét kald (`recordTraffic(…, 'event', …)`), og både
    # `/api/health` og `/api/results` summerer `p:v3:…:event:…`. Så et
    # `recentEvents > 0` **beviser** at skrivevejen virker — det er præcis den
    # vej `/api/results` læser fra.
    #
    # De to tal kan alligevel være forskellige, fordi de har forskellige
    # navnelister: `/api/results` tæller kun `RESULT_EVENTS`, mens
    # `recentEvents` tæller *alle* events. `cta-*` og `store-click` er
    # bevidst holdt ude af `RESULT_EVENTS` (de er klik og ikke resultater), så
    # «2 events» og «0 resultater» kan være sandt på samme dag.
    #
    # Det var her dommen var forkert 6/10: værktøjet skrev «TRACKING DØD» i samme
    # sætning som det citerede `recentEvents: 2`. Begge tal kom fra samme
    # skrivevej, så det modsagde sig selv og fik alle baselines i planen markeret
    # «ubekreftede» — fordi besøgende ikke *havde* brugt et værktøj, ikke fordi
    # sporingen var død.
    if recent_events > 0:
        return (
            "SPORING VIRKER — nul betyder ingen brugere fik et resultat\n"
            f"Reason: /api/health counts {recent_events} events server-side in the "
            f"last 2 days,\n"
            "written by the same /api/track path /api/results reads, so events land.\n"
            "/api/results is 0 because it only counts RESULT_EVENTS (finished runs);\n"
            "clicks and other events are deliberately excluded from that list.\n"
            f"/api/health also shows {recent_visits} visits and {recent_downloads} "
            f"downloads in 2 days.\n"
            f"A 0 baseline from these two lists is therefore REAL, not unconfirmed.\n"
            f"{LAG_NOTE}"
        )

    # Først her er sporingen faktisk død: sidevisninger lander, og *intet* event
    # gør det over to dage. Så mangler hele klientenoten, og de to lister er
    # ubekreftede.
    if recent_visits > 0:
        return (
            "TRACKING DØD (client-side events do not land, the traffic is fine)\n"
            f"Reason: /api/health shows {recent_visits} visits and {recent_downloads} "
            f"downloads in the last 2 days,\n"
            "but zero events server-side — and /api/results and /api/conversion are\n"
            "both zero for 7 days. Pageviews land and no event does, so the client\n"
            "listener is not firing. Every baseline from them is unconfirmed.\n"
            f"{LAG_NOTE}"
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
        help="run all four verdicts against fixed /api responses",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    result = check_tracking_status()
    print(result)
    return 0


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
    """All four verdicts, on the shapes /api actually returns.

    The red cases are the ones measured live 6/10. Case 1 is the exact payload
    from the live site that day: 20 visits, 55 downloads, 2 events, both windows
    zero. Before this fix it printed "TRACKING DØD" while quoting `recentEvents:
    2` — a number written by the same code path `/api/results` reads from, so it
    contradicted itself. Case 2 keeps the true dead shape (pageviews land, not a
    single event does), which is the only state that may say "død".
    """
    cases = [
        (
            "events land, nul resultater -> sporing virker",
            ZERO_RESULTS,
            ZERO_CONVERSION,
            {"stats": {"recentVisits": 20, "recentDownloads": 55,
                       "recentEvents": 2, "scans_lifetime": 53, "waitlist_lifetime": 0}},
            ("SPORING VIRKER", "2 events", "REAL, not unconfirmed"),
        ),
        (
            "besøgende, nul events -> tracking død",
            ZERO_RESULTS,
            ZERO_CONVERSION,
            {"stats": {"recentVisits": 20, "recentDownloads": 55,
                       "recentEvents": 0, "scans_lifetime": 53, "waitlist_lifetime": 0}},
            ("TRACKING DØD", "20 visits", "unconfirmed"),
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
        # En dom skal være *præcis*: «TRACKING DØD» må ikke stå i en udgave der
        # kun skal sige at sporingen virker, og omvendt. Så tæller et forkeret
        # svar også som fejl selv om den forventede sætning er med.
        forbidden = ("TRACKING DØD",) if not any("TRACKING DØD" in e for e in expected) else ()
        missing = [part for part in expected if part not in got]
        present = [part for part in forbidden if part in got]
        if missing or present:
            failed += 1
            print(f"FAIL {name}: mangler {missing}, uventet {present}\n{got}")
        else:
            print(f"OK   {name}")
    print(f"check_tracking_status --self-test: {len(cases) - failed}/{len(cases)}")
    return 1 if failed else 0


if __name__ == "__main__":
    # Uden `sys.exit` blev returværdien kasseret, så `--self-test` altid exitede 0
    # — også når den skrev FAIL. Porten `tracking-status-selftest` i
    # `tools/quality_gate.py` var dermed grøn uanset hvad selftesten fandt.
    # Resten af `tools/` bruger samme mønster, så det er husets konvention.
    sys.exit(main())
