#!/usr/bin/env python3
"""
page-profile — Zero-dependency web page profiler.

Fetches a single URL and extracts:
  - HTTP status & redirect chain
  - Title tag, meta description, canonical
  - Open Graph & Twitter Card tags
  - JSON-LD structured data (types only)
  - Heading 1-6 outline
  - Image alt-text statistics
  - Security headers (CSP, HSTS, XFO, XCTO)
  - Language, charset, hreflang
  - Overall score

No external dependencies — uses only stdlib (urllib, html.parser, json, re).
Outputs clean terminal table or JSON.
"""

import json
import re
import sys
import os
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urljoin
from collections import OrderedDict

__version__ = "1.0.0"


# ---------------------------------------------------------------------------
# Score weights (out of 20)
# ---------------------------------------------------------------------------
WEIGHTS = {
    "title_present": 2,
    "title_length_ok": 1,
    "meta_description_present": 2,
    "meta_description_length_ok": 1,
    "canonical_present": 1.5,
    "og_title_present": 1,
    "og_description_present": 1,
    "og_image_present": 1,
    "twitter_card_present": 0.5,
    "json_ld_present": 1,
    "h1_count_ok": 1,
    "images_alt_ok": 2,
    "hsts_present": 1,
    "csp_present": 1,
    "xfo_present": 0.5,
    "xcto_present": 0.5,
    "lang_present": 1,
    "charset_present": 0.5,
    "https": 1,
    "no_hreflang_issues": 0.5,
}

MAX_WEIGHT = sum(WEIGHTS.values())


# ---------------------------------------------------------------------------
# HTML Parser
# ---------------------------------------------------------------------------
class PageHTMLParser(HTMLParser):
    """Extracts metadata, headings, images, and structured data from HTML."""

    def __init__(self, base_url=""):
        super().__init__()
        self.base_url = base_url
        self.title = None
        self.meta_description = None
        self.canonical = None
        self.language = None
        self.charset = None
        self.og = {}
        self.twitter = {}
        self.json_ld_blocks = []
        self.headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
        self.images = {"total": 0, "with_alt": 0, "without_alt": 0}
        self.hreflang_links = []
        self._in_head = False
        self._in_title = False
        self._current_tag = None
        self._script_content = ""
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_lower = tag.lower()

        if tag_lower == "head":
            self._in_head = True
        elif tag_lower == "title":
            self._in_title = True
        elif tag_lower == "script" and attrs_dict.get("type", "").lower() in (
            "application/ld+json", "application/json"
        ):
            self._in_script = True
            self._script_content = ""
        elif tag_lower == "meta":
            self._handle_meta(attrs_dict)
        elif tag_lower == "link":
            self._handle_link(attrs_dict)
        elif tag_lower in self.headings:
            self.headings[tag_lower].append("")  # content appended in handle_data
            self._current_tag = tag_lower
        elif tag_lower == "img":
            self.images["total"] += 1
            alt = attrs_dict.get("alt", "").strip()
            if alt:
                self.images["with_alt"] += 1
            else:
                self.images["without_alt"] += 1
        elif tag_lower == "html" and "lang" in attrs_dict:
            self.language = attrs_dict["lang"]

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower == "head":
            self._in_head = False
        elif tag_lower == "title":
            self._in_title = False
        elif tag_lower == "script" and self._in_script:
            content = self._script_content.strip()
            if content:
                self.json_ld_blocks.append(content)
            self._in_script = False
            self._script_content = ""
        elif tag_lower in self.headings:
            self._current_tag = None

    def handle_data(self, data):
        if self._in_title:
            if self.title is None:
                self.title = data.strip()
        if self._in_script:
            self._script_content += data
        if self._current_tag:
            idx = len(self.headings[self._current_tag]) - 1
            self.headings[self._current_tag][idx] += data.strip()

    def _handle_meta(self, attrs):
        name = attrs.get("name", "").lower()
        prop = attrs.get("property", "").lower()
        charset = attrs.get("charset")
        content = attrs.get("content", "")

        if charset:
            self.charset = charset

        if name == "description" and not prop.startswith("og:"):
            self.meta_description = content
        elif name == "robots":
            pass  # not currently tracked
        elif prop == "og:title":
            self.og["title"] = content
        elif prop == "og:description":
            self.og["description"] = content
        elif prop == "og:image":
            self.og["image"] = content
        elif prop == "og:url":
            self.og["url"] = content
        elif prop == "og:type":
            self.og["type"] = content
        elif prop == "og:site_name":
            self.og["site_name"] = content
        elif name == "twitter:card":
            self.twitter["card"] = content
        elif name == "twitter:title":
            self.twitter["title"] = content
        elif name == "twitter:description":
            self.twitter["description"] = content
        elif name == "twitter:image":
            self.twitter["image"] = content
        elif name == "twitter:site":
            self.twitter["site"] = content

    def _handle_link(self, attrs):
        rel = attrs.get("rel", "").lower()
        href = attrs.get("href", "")

        if rel == "canonical":
            self.canonical = href
        elif rel == "alternate" and attrs.get("hreflang"):
            self.hreflang_links.append({
                "hreflang": attrs.get("hreflang"),
                "href": href,
            })


# ---------------------------------------------------------------------------
# Fetch page
# ---------------------------------------------------------------------------
def fetch_page(url, timeout=15):
    """Fetch a URL, follow redirects, return (status_code, headers, html, redirect_chain)."""
    redirect_chain = []
    current_url = url
    final_html = None
    final_headers = None
    final_status = None

    for i in range(10):  # max 10 redirects
        req = Request(
            current_url,
            headers={
                "User-Agent": f"page-profile/{__version__} (hermes-passiv.pages.dev)",
                "Accept": "text/html,application/xhtml+xml",
            },
            method="GET",
        )
        try:
            resp = urlopen(req, timeout=timeout)
            final_status = resp.status
            final_headers = dict(resp.headers)
            final_html = resp.read().decode("utf-8", errors="replace")
            redirect_chain.append((current_url, final_status))
            break
        except HTTPError as e:
            final_status = e.code
            final_headers = dict(e.headers)
            # Try to read error body (for redirects from http.client)
            body = e.read().decode("utf-8", errors="replace")
            redirect_chain.append((current_url, final_status))
            # Follow Location header if present
            location = e.headers.get("Location")
            if location and 300 <= e.code < 400:
                current_url = urljoin(current_url, location)
                continue
            else:
                final_html = body
                break
        except URLError as e:
            return 0, {}, str(e), redirect_chain

    return final_status, final_headers or {}, final_html or "", redirect_chain


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def analyze(url, html, headers):
    """Run all checks on fetched page data."""
    parser = PageHTMLParser(base_url=url)
    parser.feed(html)

    # Security headers (lowercase keys)
    h_lower = {k.lower(): v for k, v in headers.items()}
    sec = {
        "hsts": "strict-transport-security" in h_lower,
        "csp": "content-security-policy" in h_lower,
        "xfo": "x-frame-options" in h_lower,
        "xcto": "x-content-type-options" in h_lower,
        "referrer_policy": h_lower.get("referrer-policy", ""),
    }

    # Parse JSON-LD blocks
    json_ld_types = []
    for block in parser.json_ld_blocks:
        try:
            data = json.loads(block)
            # Could be a dict or list of dicts
            items = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
            for item in items:
                if isinstance(item, dict) and "@type" in item:
                    types = item["@type"]
                    if isinstance(types, str):
                        json_ld_types.append(types)
                    elif isinstance(types, list):
                        json_ld_types.extend(types)
        except (json.JSONDecodeError, TypeError):
            pass

    # Count total heading texts
    heading_texts = {}
    for level, texts in parser.headings.items():
        heading_texts[level] = [t for t in texts if t]

    return {
        "title": parser.title,
        "meta_description": parser.meta_description,
        "canonical": parser.canonical,
        "language": parser.language,
        "charset": parser.charset,
        "og": parser.og,
        "twitter": parser.twitter,
        "json_ld_count": len(parser.json_ld_blocks),
        "json_ld_types": json_ld_types,
        "headings": {level: [t for t in texts if t] for level, texts in parser.headings.items()},
        "images": parser.images,
        "hreflang": parser.hreflang_links,
        "security": sec,
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def score(result):
    """Compute a weighted score (0-20) and letter grade."""
    score = 0.0
    penalties = []

    # Title
    if result.get("title"):
        score += WEIGHTS["title_present"]
        tl = len(result["title"])
        if 20 <= tl <= 70:
            score += WEIGHTS["title_length_ok"]
        else:
            penalties.append(f"Title length ({tl} chars) outside recommended 20-70")
    else:
        penalties.append("Missing <title>")

    # Meta description
    md = result.get("meta_description")
    if md:
        score += WEIGHTS["meta_description_present"]
        ml = len(md)
        if 50 <= ml <= 165:
            score += WEIGHTS["meta_description_length_ok"]
        else:
            penalties.append(f"Meta description length ({ml} chars) outside recommended 50-165")
    else:
        penalties.append("Missing meta description")

    # Canonical
    if result.get("canonical"):
        score += WEIGHTS["canonical_present"]

    # OG tags
    og = result.get("og", {})
    if og.get("title"):
        score += WEIGHTS["og_title_present"]
    if og.get("description"):
        score += WEIGHTS["og_description_present"]
    if og.get("image"):
        score += WEIGHTS["og_image_present"]

    # Twitter card
    tw = result.get("twitter", {})
    if tw.get("card"):
        score += WEIGHTS["twitter_card_present"]

    # JSON-LD
    if result.get("json_ld_count", 0) > 0:
        score += WEIGHTS["json_ld_present"]

    # Headings
    h1_count = len(result.get("headings", {}).get("h1", []))
    if h1_count == 1:
        score += WEIGHTS["h1_count_ok"]
    elif h1_count > 1:
        penalties.append(f"Multiple H1 tags ({h1_count}) — should be exactly 1")
    else:
        penalties.append("Missing H1 tag")

    # Image alt text
    imgs = result.get("images", {"total": 0, "with_alt": 0, "without_alt": 0})
    if imgs["total"] > 0:
        ratio = imgs["with_alt"] / imgs["total"]
        if ratio >= 0.9:
            score += WEIGHTS["images_alt_ok"]
        elif ratio >= 0.5:
            score += WEIGHTS["images_alt_ok"] * 0.5
        else:
            penalties.append(f"Low alt-text coverage: {imgs['with_alt']}/{imgs['total']} images have alt")
    elif imgs["total"] == 0:
        score += WEIGHTS["images_alt_ok"]  # no images = no problem

    # Security headers
    sec = result.get("security", {})
    for key, weight_key in [("hsts", "hsts_present"), ("csp", "csp_present"),
                             ("xfo", "xfo_present"), ("xcto", "xcto_present")]:
        if sec.get(key):
            score += WEIGHTS[weight_key]

    # Language
    if result.get("language"):
        score += WEIGHTS["lang_present"]

    # Charset
    if result.get("charset"):
        score += WEIGHTS["charset_present"]

    # Hreflang
    hf = result.get("hreflang", [])
    if len(hf) > 0:
        score += WEIGHTS["no_hreflang_issues"]  # present = good

    score = round(score, 1)

    # Grade
    pct = score / MAX_WEIGHT * 100
    if pct >= 90:
        grade = "A"
    elif pct >= 75:
        grade = "B"
    elif pct >= 55:
        grade = "C"
    elif pct >= 35:
        grade = "D"
    else:
        grade = "F"

    return score, MAX_WEIGHT, grade, penalties


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def _status_icon(passed):
    return "✅" if passed else "❌"


def _warn_icon(level="warn"):
    return "⚠️"


def _fmt_val(val, default="—"):
    return val if val else default


# ---------------------------------------------------------------------------
# Terminal output
# ---------------------------------------------------------------------------
def format_terminal(url, status, redirect_chain, result, score, max_score, grade, penalties):
    lines = []
    sep = "─" * 54

    lines.append("")
    lines.append(f"  page-profile v{__version__}  —  {url}")
    lines.append(f"  status: {_status_icon(status == 200)} HTTP {status}")
    lines.append(sep)

    # Title
    title = result.get("title")
    if title:
        tl = len(title)
        ok = "✅" if 20 <= tl <= 70 else _warn_icon()
        lines.append(f"  Title:        {ok} {title[:70]}")
        lines.append(f"                 ({tl} chars)")
    else:
        lines.append(f"  Title:        ❌ Missing")

    # Meta description
    md = result.get("meta_description")
    if md:
        ml = len(md)
        ok = "✅" if 50 <= ml <= 165 else _warn_icon()
        lines.append(f"  Description:  {ok} {md[:80]}…" if len(md) > 80 else f"  Description:  {ok} {md}")
        lines.append(f"                 ({ml} chars)")
    else:
        lines.append(f"  Description:  ❌ Missing")

    # Canonical
    can = result.get("canonical")
    lines.append(f"  Canonical:    {_status_icon(bool(can))} {_fmt_val(can)}")

    # Language
    lang = result.get("language")
    lines.append(f"  Language:     {_status_icon(bool(lang))} {_fmt_val(lang)}")

    # Charset
    cs = result.get("charset")
    lines.append(f"  Charset:      {_status_icon(bool(cs))} {_fmt_val(cs)}")

    lines.append(sep)

    # Open Graph
    og = result.get("og", {})
    lines.append(f"  Open Graph:")
    lines.append(f"    og:title       {_status_icon(bool(og.get('title')))} {_fmt_val(og.get('title', ''))[:60]}")
    lines.append(f"    og:description {_status_icon(bool(og.get('description')))} {_fmt_val(og.get('description', ''))[:60]}")
    lines.append(f"    og:image       {_status_icon(bool(og.get('image')))} {_fmt_val(og.get('image', ''))[:60]}")
    if og.get("type"):
        lines.append(f"    og:type        {og['type']}")

    tw = result.get("twitter", {})
    lines.append(f"  Twitter Card:")
    lines.append(f"    twitter:card  {_status_icon(bool(tw.get('card')))} {_fmt_val(tw.get('card', ''))}")
    if tw.get("title"):
        lines.append(f"    twitter:title {tw['title'][:60]}")

    lines.append(sep)

    # JSON-LD
    jl = result.get("json_ld_count", 0)
    types = result.get("json_ld_types", [])
    icon = "✅" if jl > 0 else "—"
    lines.append(f"  JSON-LD:      {icon} {jl} block{'s' if jl != 1 else ''}"
                  f"{' (' + ', '.join(types[:5]) + ')' if types else ''}")

    lines.append(sep)

    # Headings
    hdgs = result.get("headings", {})
    lines.append(f"  Headings:")
    for level in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        texts = hdgs.get(level, [])
        if level == "h1":
            count = len(texts)
            if count == 1:
                icon = "✅"
            elif count == 0:
                icon = "❌"
            else:
                icon = "⚠️"
            lines.append(f"    {level}: {icon} {count} — {texts[0][:55] if texts else '<none>'}")
        elif texts:
            lines.append(f"    {level}: {len(texts)} — {texts[0][:55]}")

    lines.append(sep)

    # Images
    imgs = result.get("images", {})
    total = imgs.get("total", 0)
    with_alt = imgs.get("with_alt", 0)
    without_alt = imgs.get("without_alt", 0) if total > 0 else 0
    if total > 0:
        pct = (with_alt / total) * 100
        icon = "✅" if pct >= 90 else "⚠️"
        lines.append(f"  Images:       {icon} {total} total, {with_alt} with alt ({pct:.0f}%)")
        if without_alt > 0:
            lines.append(f"                 {without_alt} missing alt text")
    else:
        lines.append(f"  Images:       — 0 images found")

    lines.append(sep)

    # Security headers
    sec = result.get("security", {})
    lines.append(f"  Security Headers:")
    for name, key, warn_if_missing in [
        ("HSTS", "hsts", True),
        ("CSP",  "csp", True),
        ("X-Frame-Options", "xfo", False),
        ("X-Content-Type-Options", "xcto", False),
    ]:
        if sec.get(key):
            lines.append(f"    {name}: {'✅' * 2} Present")
        elif warn_if_missing:
            lines.append(f"    {name}: {'⚠️'} Missing (recommended)")
        else:
            lines.append(f"    {name}: {'—'} Missing (optional)")
    if sec.get("referrer_policy"):
        lines.append(f"    Referrer-Policy: {sec['referrer_policy']}")

    lines.append(sep)

    # Hreflang
    hf = result.get("hreflang", [])
    if hf:
        lines.append(f"  Hreflang:     ✅ {len(hf)} alternate{'' if len(hf) == 1 else 's'}")
        for h in hf[:5]:
            lines.append(f"                 {h['hreflang']} → {h['href']}")
    else:
        lines.append(f"  Hreflang:     — None")

    # Redirect chain
    if len(redirect_chain) > 1:
        lines.append(f"  Redirects:    {' → '.join([f'{s[1]}' for s in redirect_chain])}")
        for src, code in redirect_chain:
            lines.append(f"                 {code} {src}")
    else:
        lines.append(f"  Redirects:    — Direct ({status})")

    lines.append(sep)

    # Score
    lines.append(f"  Score:        {score}/{max_score}  Grade: {grade}")
    if penalties:
        for p in penalties:
            lines.append(f"                 ⚠️  {p}")

    lines.append(sep)
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------
def format_json(url, status, redirect_chain, result, score, max_score, grade, penalties):
    data = OrderedDict()
    data["url"] = url
    data["status"] = status
    data["redirects"] = [{"url": u, "status": s} for u, s in redirect_chain]
    data["title"] = result.get("title")
    data["title_length"] = len(result.get("title", "")) if result.get("title") else None
    data["meta_description"] = result.get("meta_description")
    data["meta_description_length"] = len(result.get("meta_description", "")) if result.get("meta_description") else None
    data["canonical"] = result.get("canonical")
    data["language"] = result.get("language")
    data["charset"] = result.get("charset")
    data["og"] = {k: v for k, v in result.get("og", {}).items()}
    data["twitter"] = {k: v for k, v in result.get("twitter", {}).items()}
    data["json_ld_count"] = result.get("json_ld_count", 0)
    data["json_ld_types"] = result.get("json_ld_types", [])
    data["headings"] = {k: v for k, v in result.get("headings", {}).items()}
    data["images"] = result.get("images", {})
    data["hreflang"] = result.get("hreflang", [])
    data["security"] = result.get("security", {})
    data["score"] = score
    data["max_score"] = max_score
    data["grade"] = grade
    data["penalties"] = penalties
    return json.dumps(data, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="page-profile — Zero-dependency web page profiler",
    )
    parser.add_argument("url", help="URL to profile (e.g., https://example.com)")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of terminal report")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds (default: 15)")
    parser.add_argument("--version", action="version", version=f"page-profile v{__version__}")

    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith(("http://", "https://")):
        args.url = "https://" + args.url

    # Fetch
    status_code, headers, html, redirect_chain = fetch_page(args.url, timeout=args.timeout)

    if status_code == 0:
        print(f"Error: {html}")
        sys.exit(1)

    # Analyze
    result = analyze(args.url, html, headers)

    # Score
    sc, max_sc, grade, penalties = score(result)

    # Output
    if args.json:
        print(format_json(args.url, status_code, redirect_chain, result, sc, max_sc, grade, penalties))
    else:
        print(format_terminal(args.url, status_code, redirect_chain, result, sc, max_sc, grade, penalties))


if __name__ == "__main__":
    main()