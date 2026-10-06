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
    
    # Both endpoints show zero activity - check if we can confirm it's really zero
    recent_visits = health_data.get("recentVisits", 0)
    
    if recent_visits > 0:
        return (
            "0 = ubekreftet (zero is unconfirmed)\n"
            f"Reason: /api/health shows {recent_visits} recent visits (last 2 days),\n"
            "but both /api/results and /api/conversion show zero activity for 7 days.\n"
            "This indicates tracking is broken (tracking død) for recent visitors."
        )
    else:
        # No recent visits detected, but we can't be certain there are no visitors at all
        # (they might have visited more than 2 days ago but less than 28 days ago)
        recent_visits = health_data.get("stats", {}).get("recentVisits", 0)
        scans_lifetime = health_data.get("stats", {}).get("scans_lifetime", 0)
        waitlist_lifetime = health_data.get("stats", {}).get("waitlist_lifetime", 0)
        
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
    args = parser.parse_args()
    
    result = check_tracking_status()
    print(result)


if __name__ == "__main__":
    main()