#!/usr/bin/env python3
"""
scan.py — CLI wrapper around scanner_core.

usage:
    python scan.py <url> [more-urls...]
    python scan.py --file page.html
    python scan.py <url> --crawl N     # site audit: follow same-origin links, max N pages (1-200)

Outputs a human-readable report (and machine JSON with --json).
Exit code 1 if any scanned page has errors, 0 otherwise.
"""

import json
import sys

from scanner_core import scan_url, scan_html, crawl_site


def render(rep: dict) -> str:
    if not rep.get("ok"):
        return f"SCAN FAILED for {rep.get('url', '?')}: {rep.get('error')}"
    lines = [
        f"EAA/WCAG report — {rep['url']}",
        f"Score: {rep['score']}/100  Grade {rep['grade']} "
        f"(errors={rep['summary']['errors']}, warnings={rep['summary']['warnings']}, "
        f"notices={rep['summary']['notices']})",
        "-" * 60,
    ]
    for f in rep["findings"]:
        lines.append(f"[{f['severity'].upper():7}] {f['rule_id']}: {f['message']}")
        for ex in f["examples"]:
            lines.append(f"           e.g. {ex}")
    if not rep["findings"]:
        lines.append("No issues found by the automated checks.")
    lines.append("")
    lines.append("Note: automated checks catch ~30-40% of accessibility issues.")
    lines.append("Full manual checklist: see 'EAA Compliance Checklist' e-book.")
    return "\n".join(lines)


def render_site(result: dict) -> str:
    agg = result["aggregate"]
    lines = [
        f"SITE REPORT — {agg['pagesScanned']} page(s) scanned, "
        f"{agg['pagesFailed']} failed",
        f"Average score: {agg['averageScore']}/100  Grade {agg['grade']}",
        f"Totals: errors={agg['totalErrors']} "
        f"warnings={agg['totalWarnings']} notices={agg['totalNotices']}",
        "-" * 60,
    ]
    if agg["rulesByFrequency"]:
        lines.append("Issues across the site (most frequent first):")
        for rid, n in agg["rulesByFrequency"]:
            lines.append(f"  {n:5}x  {rid}")
    else:
        lines.append("No issues found by the automated checks.")
    if agg["worstPage"]:
        lines.append(
            f"Worst page: {agg['worstPage']['target']} "
            f"({agg['worstPage']['score']}/100)")
    lines.append("-" * 60)
    for p in result["pages"]:
        if p.get("ok"):
            lines.append(f"[{p['score']:3}/100 {p.get('grade', '?')}] {p['target']}")
        else:
            lines.append(f"[FAILED] {p.get('target', '?')}: {p.get('error')}")
    lines.append("")
    lines.append("Note: automated checks catch ~30-40% of accessibility issues.")
    return "\n".join(lines)


def main():
    args = sys.argv[1:]
    as_json = "--json" in args
    crawl_n = None
    if "--crawl" in args:
        i = args.index("--crawl")
        try:
            crawl_n = int(args[i + 1])
        except (IndexError, ValueError):
            print("--crawl requires a number of pages (1-200)"); sys.exit(2)
        del args[i:i + 2]
        if not 1 <= crawl_n <= 200:
            print("--crawl must be between 1 and 200 pages"); sys.exit(2)
    args = [a for a in args if a != "--json"]
    if not args:
        print(__doc__)
        sys.exit(2)

    if crawl_n is not None:
        url = args[0]
        def on_page(rep, done, total):
            print(f"[{done}/{total}] {rep.get('target', '?')} -> "
                  f"{rep.get('score') if rep.get('ok') else 'FAILED'}",
                  file=sys.stderr)
        result = crawl_site(url, max_pages=crawl_n, on_page=on_page)
        print(render_site(result) if not as_json
              else json.dumps(result, indent=2))
        agg = result["aggregate"]
        sys.exit(1 if agg["pagesFailed"] or agg["totalErrors"] > 0 else 0)

    reports = []
    for arg in args:
        try:
            if arg.startswith("http"):
                rep = scan_url(arg)
            else:
                with open(arg, encoding="utf-8") as fh:
                    rep = scan_html(fh.read())
                rep["url"] = arg
        except Exception as e:
            rep = {"ok": False, "error": str(e), "url": arg}
        reports.append(rep)
        if not as_json:
            print(render(rep))
            print()

    if as_json:
        print(json.dumps(reports, indent=2))
    sys.exit(1 if any(r.get("summary", {}).get("errors", 0) > 0
                      or not r.get("ok") for r in reports) else 0)


if __name__ == "__main__":
    main()
