#!/usr/bin/env python3
"""gen_sitemap.py — regenerates site/sitemap.xml from the actual HTML files.

- Walks site/ for .html files, maps to extensionless URLs (Cloudflare Pages 308s).
- Skips files starting with _.
- lastmod = file mtime (UTC date).
- Adds xhtml:link hreflang alternates for EN<->DA pairs via hreflang_pairs.json
  (keys/values are slugs; EN slugs map to DA blog slugs and vice versa).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
BASE = "https://hermes-passiv.pages.dev"

pairs = {}
pf = SITE / "hreflang_pairs.json"
if pf.exists():
    try:
        data = json.loads(pf.read_text())
        if isinstance(data, dict):
            pairs = data
    except Exception as e:
        print(f"WARN: could not parse hreflang_pairs.json: {e}")

rev = {v: k for k, v in pairs.items()}


def url_for(path):
    rel = path.relative_to(SITE).as_posix()
    if path.name.startswith("_") or "/_" in rel:
        return None
    if not rel.endswith(".html"):
        return None
    slug = rel[:-5]
    if slug.endswith("/index"):
        slug = slug[: -len("/index")]
    if slug == "index":
        return "/"
    return "/" + slug


def find_pair(url):
    """Return (lang_of_url, other_url) or (None, None)."""
    slug_path = url.strip("/")
    last = slug_path.split("/")[-1]
    is_da = "/da/" in url or url.endswith("-da")
    if not is_da:
        da_slug = pairs.get(slug_path) or pairs.get(last)
        if da_slug:
            # EN entry: pair lives under /da/blog/<slug>
            return "en", f"/da/blog/{da_slug}"
    else:
        en_slug = rev.get(last)
        if en_slug:
            return "da", f"/blog/{en_slug}"
    return None, None


def priority_freq(url):
    if url == "/":
        return "daily", "1.0"
    parts = url.strip("/").split("/")
    top = parts[0]
    if top in ("blog", "guides"):
        return "monthly", "0.7"
    return "weekly", "0.9"


entries = []
for path in sorted(SITE.rglob("*.html")):
    url = url_for(path)
    if not url:
        continue
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    lastmod = mtime.strftime("%Y-%m-%d")
    freq, pri = priority_freq(url)
    lang, pair_url = find_pair(url)
    alt = ""
    if lang and pair_url:
        other = "da" if lang == "en" else "en"
        alt = (
            f'\n    <xhtml:link rel="alternate" hreflang="{lang}" href="{BASE}{url}"/>'
            f'\n    <xhtml:link rel="alternate" hreflang="{other}" href="{BASE}{pair_url}"/>'
        )
    entries.append(
        f"  <url>\n    <loc>{BASE}{url}</loc>\n"
        f"    <lastmod>{lastmod}</lastmod>\n"
        f"    <changefreq>{freq}</changefreq>\n"
        f"    <priority>{pri}</priority>{alt}\n  </url>"
    )

xml = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
    '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + "\n".join(entries)
    + "\n</urlset>\n"
)

out = SITE / "sitemap.xml"
out.write_text(xml)
print(f"Sitemap regenerated: {len(entries)} URLs -> {out}")
