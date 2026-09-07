#!/usr/bin/env python3
"""SEO / structure check for the built sites.

    python tools/seo_check.py                       # scan dist/<domain>/**/*.html
    python tools/seo_check.py --only mahope.tools
    python tools/seo_check.py --url https://cleancopy.tools/ https://cleancopy.tools/da/   # live pages
    python tools/seo_check.py --verbose             # list every finding

Checks per page: one <title> (<=60 chars, unique per site), meta description (<=160),
canonical, hreflang en/da/x-default where a translation exists, Open Graph
(title/description/image/url/site_name/type), twitter:card, JSON-LD present,
exactly one <h1>, <header>/<main>/<nav>/<footer>, <img alt>, viewport, lang,
favicon + manifest, no <style> rules on design-system selectors, no leftover
old-origin URLs, no inline hex colours in style="" attributes.
Exit code 1 when anything is missing.
"""
from __future__ import annotations

import argparse
import html as htmllib
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
OLD_ORIGIN = "hermes-passiv.pages.dev"


def find(text: str, rx: str, flags=re.I | re.S) -> list[str]:
    return re.findall(rx, text, flags)


def check_page(text: str, name: str) -> list[str]:
    errs: list[str] = []
    head_m = re.search(r"<head\b.*?</head>", text, re.S | re.I)
    head = head_m.group(0) if head_m else text[:8000]

    titles = find(head, r"<title>(.*?)</title>")
    if len(titles) != 1:
        errs.append(f"title count {len(titles)}")
    elif len(htmllib.unescape(titles[0]).strip()) > 60:
        errs.append(f"title {len(htmllib.unescape(titles[0]).strip())} chars")
    elif len(titles[0].strip()) < 10:
        errs.append("title too short")

    desc = find(head, r'<meta\s+name="description"\s+content="([^"]*)"')
    if len(desc) != 1:
        errs.append(f"description count {len(desc)}")
    elif len(htmllib.unescape(desc[0])) > 160:
        errs.append(f"description {len(htmllib.unescape(desc[0]))} chars")
    elif len(desc[0]) < 40:
        errs.append("description too short")

    canon = find(head, r'<link\s+rel="canonical"\s+href="([^"]*)"')
    if len(canon) != 1:
        errs.append(f"canonical count {len(canon)}")
    elif not canon[0].startswith("https://") or OLD_ORIGIN in canon[0]:
        errs.append(f"canonical bad {canon[0]}")

    hl = dict((l.lower(), h) for l, h in find(head, r'<link\s+rel="alternate"\s+hreflang="([^"]+)"\s+href="([^"]+)"'))
    if hl:
        if "x-default" not in hl:
            errs.append("hreflang: no x-default")
        if not ("en" in hl and "da" in hl):
            errs.append("hreflang: not both en+da")
        if canon and canon[0] not in hl.values():
            errs.append("hreflang: canonical not among alternates")

    ogs = dict((k.lower(), v) for k, v in find(head, r'<meta\s+(?:property|name)="((?:og|twitter):[\w:]+)"\s+content="([^"]*)"'))
    for k in ("og:title", "og:description", "og:image", "og:url", "og:site_name", "og:type", "twitter:card"):
        if not ogs.get(k):
            errs.append(f"missing {k}")
    if canon and ogs.get("og:url") and ogs["og:url"] != canon[0]:
        errs.append("og:url != canonical")
    if ogs.get("og:image") and not ogs["og:image"].startswith("https://"):
        errs.append("og:image not absolute")

    if not find(head, r'<script\s+type="application/ld\+json"'):
        errs.append("no JSON-LD")
    if not find(head, r'<meta\s+name="viewport"'):
        errs.append("no viewport")
    if not re.search(r'<html[^>]*\slang="(en|da)"', text[:400], re.I):
        errs.append("no html lang")
    if not find(head, r'<link\s+rel="icon"'):
        errs.append("no favicon")
    if not find(head, r'<link\s+rel="manifest"'):
        errs.append("no manifest")

    body = text[head_m.end():] if head_m else text
    body = re.sub(r"<(script|pre|textarea)\b.*?</\1>", "", body, flags=re.S | re.I)
    body = re.sub(r'href="javascript:[^"]*"', "", body, flags=re.I)
    n_h1 = len(find(body, r"<h1\b"))
    if n_h1 != 1:
        errs.append(f"h1 count {n_h1}")
    for tag in ("header", "main", "nav", "footer"):
        if not find(body, rf"<{tag}\b"):
            errs.append(f"no <{tag}>")
    if len(find(body, r'<main\b')) != 1:
        errs.append("main count != 1")
    for img in find(body, r"<img\b[^>]*>"):
        if not re.search(r'\salt="', img):
            errs.append(f"img without alt: {img[:60]}")
    if not find(body, r'<button\s+class="nav-toggle"[^>]*aria-expanded='):
        errs.append("no mobile nav toggle")
    if OLD_ORIGIN in text:
        errs.append(f"old origin {OLD_ORIGIN} still referenced")
    for css in find(body + head, r"<style\b[^>]*>(.*?)</style>"):
        for sel in re.findall(r"(?:^|\})\s*([^{}@]+?)\s*\{", css):
            for part in sel.split(","):
                if part.strip() in ("body", "h1", "h2", ".container", ".card", ".btn-primary", ":root", "*", "pre.cmd", ".compare"):
                    errs.append(f"page css redefines {part.strip()}")
    for sty in find(body, r'\sstyle="([^"]*)"'):
        if re.search(r"#[0-9a-f]{3,6}\b", sty, re.I):
            errs.append(f"inline hex colour: {sty[:50]}")
    return errs


def scan_dist(only: str | None) -> tuple[int, int, dict]:
    total = pages = 0
    report: dict[str, list[str]] = {}
    for domain_dir in sorted(DIST.iterdir()):
        if not domain_dir.is_dir() or (only and domain_dir.name != only):
            continue
        seen_titles: dict[str, set] = defaultdict(set)
        seen_canon: defaultdict = defaultdict(list)
        for p in sorted(domain_dir.rglob("*.html")):
            rel = p.relative_to(domain_dir).as_posix()
            if rel.endswith("404.html"):
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            errs = check_page(text, rel)
            t = find(text, r"<title>(.*?)</title>")
            c = find(text, r'<link\s+rel="canonical"\s+href="([^"]*)"')
            if t:
                seen_titles[t[0].strip()].add(c[0] if c else rel)
            if c:
                seen_canon[c[0]].append(rel)
            pages += 1
            if errs:
                report[f"{domain_dir.name}/{rel}"] = errs
                total += len(errs)
        for title, canons in seen_titles.items():
            if len(canons) > 1 and title:
                report[f"{domain_dir.name} (title x{len(canons)})"] = [f"duplicate title: {title}"]
                total += 1
        for canon, files in seen_canon.items():
            if len(files) > 1 and not (len(files) == 2 and canon.rstrip("/").endswith(("tools", ".dev", ".com", "/da"))):
                report[f"{domain_dir.name} (canonical)"] = [f"shared canonical {canon}: {files}"]
                total += 1
    return total, pages, report


def scan_urls(urls: list[str]) -> tuple[int, int, dict]:
    total = pages = 0
    report = {}
    for u in urls:
        req = urllib.request.Request(u, headers={"User-Agent": "seo_check/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", errors="ignore")
        errs = check_page(text, u)
        pages += 1
        if errs:
            report[u] = errs
            total += len(errs)
    return total, pages, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--url", nargs="*")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    total, pages, report = scan_urls(a.url) if a.url else scan_dist(a.only)
    kinds: Counter = Counter()
    for errs in report.values():
        for e in errs:
            kinds[re.sub(r"[:\d].*", "", e).strip()] += 1
    for k, n in kinds.most_common():
        print(f"{n:5d}  {k}")
    if a.verbose or len(report) <= 25:
        for page, errs in report.items():
            print(f"- {page}")
            for e in errs:
                print(f"    {e}")
    print(f"\n{pages} pages, {total} findings on {len(report)} pages")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
