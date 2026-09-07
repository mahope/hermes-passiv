#!/usr/bin/env python3
"""Screenshots and horizontal-overflow check for the built sites (or live URLs).

    python tools/shots.py                    # overflow check of every dist page at 360px + screenshots of samples
    python tools/shots.py --widths 360 768 1280 --pages / /da/ /blog/foo --only mahope.tools
    python tools/shots.py --live https://cleancopy.tools/ https://cleancopy.tools/da/ --widths 360

dist/ pages are served in-process by routing requests to files (clean URLs like Pages).
Screenshots land in dist/_shots/<domain>/<width>-<slug>.png.
"""
from __future__ import annotations

import argparse
import mimetypes
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SHOTS = DIST / "_shots"
OVERFLOW_JS = """(() => { const W = document.documentElement.clientWidth; let m = 0;
  for (const e of document.querySelectorAll('body *')) {
    let a = e.parentElement, inScroll = false;
    while (a && a !== document.body) { const o = getComputedStyle(a).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden' || o === 'clip') { inScroll = true; break; } a = a.parentElement; }
    if (inScroll) continue; const r = e.getBoundingClientRect(); if (r.width > 0) m = Math.max(m, r.right - W); }
  return Math.round(Math.max(m, document.documentElement.scrollWidth - W)); })()"""
SAMPLE = {
    "cleancopy.tools": ["/", "/da/", "/clean-copy-tool", "/blog/copy-table-from-pdf-to-excel", "/clean-copy-cli-ref", "/404.html"],
    "deskuptime.com": ["/", "/da/", "/tools/", "/security-headers-checker/"],
    "bugbottle.dev": ["/", "/da/", "/bugbottle-demo", "/blog/bug-reports-in-ci-pipeline"],
    "mahope.tools": ["/", "/da/", "/free-tools", "/json-formatter", "/contrast-checker", "/blog/gdpr-fines-2026",
                     "/da/blog/gdpr-boeder-2026", "/books/", "/books/eaa-checklist", "/guides/wix-accessibility-check",
                     "/dpa-generator", "/compliance-guide", "/404.html"],
}


def file_for(dist: Path, path: str) -> Path | None:
    p = path.split("?")[0]
    cands = [dist / p.lstrip("/")]
    if p.endswith("/"):
        cands = [dist / (p.lstrip("/") + "index.html")]
    elif "." not in p.rsplit("/", 1)[-1]:
        cands = [dist / (p.lstrip("/") + ".html"), dist / (p.lstrip("/") + "/index.html")]
    for c in cands:
        if c.is_file():
            return c
    return None


def serve(dist: Path, domain: str):
    def handler(route, request):
        url = request.url
        m = re.match(rf"https://{re.escape(domain)}(/.*)?$", url)
        if not m:
            return route.continue_()
        f = file_for(dist, m.group(1) or "/")
        if not f:
            return route.fulfill(status=404, body=(dist / "404.html").read_bytes(), content_type="text/html")
        ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        if f.suffix == ".webmanifest":
            ctype = "application/manifest+json"
        return route.fulfill(status=200, body=f.read_bytes(), content_type=ctype)
    return handler


def slug(path: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.strip("/").lower()).strip("-") or "home"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--widths", nargs="*", type=int, default=[360, 768, 1280])
    ap.add_argument("--pages", nargs="*")
    ap.add_argument("--only")
    ap.add_argument("--live", nargs="*")
    ap.add_argument("--no-overflow-scan", action="store_true")
    a = ap.parse_args()
    problems: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        if a.live:
            ctx = browser.new_context(viewport={"width": a.widths[0], "height": 800})
            page = ctx.new_page()
            for u in a.live:
                m = re.match(r"https://([^/]+)(/.*)?", u)
                d = SHOTS / m.group(1)
                d.mkdir(parents=True, exist_ok=True)
                for w in a.widths:
                    page.set_viewport_size({"width": w, "height": 800})
                    page.goto(u, wait_until="load")
                    page.wait_for_timeout(600)
                    over = page.evaluate(OVERFLOW_JS)
                    out = d / f"live-{w}-{slug(m.group(2) or '/')}.png"
                    page.screenshot(path=str(out), full_page=(w != 360))
                    print(f"{u} @{w}: overflow={over}px -> {out}")
                    if over > 0:
                        problems.append(f"{u} @{w}: {over}px")
            browser.close()
        else:
            for domain_dir in sorted(DIST.iterdir()):
                domain = domain_dir.name
                if domain.startswith("_") or not domain_dir.is_dir() or (a.only and domain != a.only):
                    continue
                ctx = browser.new_context(viewport={"width": 360, "height": 800})
                ctx.route("**/*", serve(domain_dir, domain))
                page = ctx.new_page()
                if not a.no_overflow_scan and not a.pages:
                    for f in sorted(domain_dir.rglob("*.html")):
                        rel = "/" + f.relative_to(domain_dir).as_posix()
                        page.goto(f"https://{domain}{rel}", wait_until="load")
                        over = page.evaluate(OVERFLOW_JS)
                        if over > 0:
                            problems.append(f"{domain}{rel} @360: {over}px")
                    print(f"{domain}: overflow scan done ({len([p for p in problems if p.startswith(domain)])} problems)")
                d = SHOTS / domain
                d.mkdir(parents=True, exist_ok=True)
                for path in (a.pages or SAMPLE.get(domain, ["/"])):
                    for w in a.widths:
                        page.set_viewport_size({"width": w, "height": 800})
                        page.goto(f"https://{domain}{path}", wait_until="load")
                        page.wait_for_timeout(300)
                        over = page.evaluate(OVERFLOW_JS)
                        out = d / f"{w}-{slug(path)}.png"
                        page.screenshot(path=str(out), full_page=(w == 360))
                        if over > 0:
                            problems.append(f"{domain}{path} @{w}: {over}px")
                        if w == 360 and path in ("/", "/da/"):  # open the mobile menu once
                            page.click(".nav-toggle")
                            page.wait_for_timeout(250)
                            page.screenshot(path=str(d / f"{w}-{slug(path)}-menu.png"))
                ctx.close()
            browser.close()
    print("\nHorizontal overflow:" if problems else "\nNo horizontal overflow.")
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
