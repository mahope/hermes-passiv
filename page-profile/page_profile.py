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

__version__ = "1.1.0"

# ---------------------------------------------------------------------------
# License (Pro) — offline key validation, no network calls.
# A Pro key is "PPRO-" followed by 32 base32 chars; the last 8 are a checksum
# of the first 24 + salt, so random strings are rejected without phoning home.
# ---------------------------------------------------------------------------
_LICENSE_SALT = "page-profile-pro-v1"
LICENSE_FILE = os.path.join(os.path.expanduser("~"), ".page-profile-license")


def _b32_checksum(payload: str) -> str:
    import hashlib
    import base64
    digest = hashlib.sha256((_LICENSE_SALT + payload).encode()).digest()
    return base64.b32encode(digest).decode()[:8]


def make_license_key(seed: str) -> str:
    """Generate a valid Pro key from a customer seed (used by the seller)."""
    payload = "".join(c for c in seed.upper() if c.isalnum())[:24].ljust(24, "X")
    return "PPRO-" + payload + _b32_checksum(payload)


def validate_license_key(key: str) -> bool:
    if not key or not key.startswith("PPRO-") or len(key) != len("PPRO-") + 32:
        return False
    payload = key[5:29]
    return _b32_checksum(payload) == key[29:]


def load_license() -> str:
    """Read stored license key from env var or ~/.page-profile-license."""
    key = os.environ.get("PAGE_PROFILE_LICENSE", "")
    if not key and os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE) as f:
                key = f.read().strip()
        except OSError:
            pass
    return key


def require_pro(feature: str) -> str:
    """Return a valid license key or exit with an upgrade message."""
    key = load_license()
    if key and validate_license_key(key):
        return key
    print(f"Error: '{feature}' is a page-profile Pro feature.", file=sys.stderr)
    print("Get a Pro license at https://hermes-passiv.pages.dev/page-profile ($19/year).", file=sys.stderr)
    print("Then run:  page-profile --activate YOUR-KEY   (or set PAGE_PROFILE_LICENSE)", file=sys.stderr)
    sys.exit(2)


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
# ---------------------------------------------------------------------------
# Pro features
# ---------------------------------------------------------------------------

def _profile_url(url, timeout=15):
    """Fetch + analyze + score one URL. Returns dict or raises RuntimeError."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    status_code, headers, html, redirect_chain = fetch_page(url, timeout=timeout)
    if status_code == 0:
        raise RuntimeError(f"Could not fetch {url}: {html}")
    result = analyze(url, html, headers)
    sc, max_sc, grade, penalties = score(result)
    return {
        "url": url, "status": status_code, "redirects": redirect_chain,
        "result": result, "score": sc, "max_score": max_sc,
        "grade": grade, "penalties": penalties,
    }


def run_compare(url_a, url_b, timeout=15):
    """Pro: side-by-side diff of two URLs' key signals."""
    a = _profile_url(url_a, timeout)
    b = _profile_url(url_b, timeout)

    def row(label, va, vb, ok_when_equal=True):
        same = (va == vb)
        icon = "✅" if (same == ok_when_equal or not ok_when_equal and same) else ("✅" if same else "⚠️ ")
        return f"  {label:<22} {'=' if same else '≠'}  A: {_fmt_val(va)}   B: {_fmt_val(vb)}"

    lines = []
    sep = "─" * 78
    lines.append("")
    lines.append(f"  page-profile v{__version__} — COMPARE (Pro)")
    lines.append(f"  A: {a['url']}  →  score {a['score']}/{a['max_score']} ({a['grade']})")
    lines.append(f"  B: {b['url']}  →  score {b['score']}/{b['max_score']} ({b['grade']})")
    lines.append(sep)
    pairs = [
        ("Title", a["result"].get("title"), b["result"].get("title")),
        ("Description", a["result"].get("meta_description"), b["result"].get("meta_description")),
        ("Canonical", a["result"].get("canonical"), b["result"].get("canonical")),
        ("Language", a["result"].get("language"), b["result"].get("language")),
        ("OG image", a["result"].get("og", {}).get("image"), b["result"].get("og", {}).get("image")),
        ("Twitter card", a["result"].get("twitter", {}).get("card"), b["result"].get("twitter", {}).get("card")),
        ("JSON-LD blocks", a["result"].get("json_ld_count", 0), b["result"].get("json_ld_count", 0)),
        ("H1 count", len(a["result"].get("headings", {}).get("h1", [])), len(b["result"].get("headings", {}).get("h1", []))),
        ("Images total", a["result"].get("images", {}).get("total", 0), b["result"].get("images", {}).get("total", 0)),
        ("Images w/ alt", a["result"].get("images", {}).get("with_alt", 0), b["result"].get("images", {}).get("with_alt", 0)),
        ("HSTS", a["result"].get("security", {}).get("hsts"), b["result"].get("security", {}).get("hsts")),
        ("CSP", a["result"].get("security", {}).get("csp"), b["result"].get("security", {}).get("csp")),
    ]
    for label, va, vb in pairs:
        sa = _fmt_val(va)
        sb = _fmt_val(vb)
        marker = "=" if va == vb else "≠"
        flag = "" if va == vb else ("   ← differs" )
        lines.append(f"  {marker} {label:<20} A: {str(sa)[:38]:<38} B: {str(sb)[:38]}{flag}")
    lines.append(sep)
    d = round(a["score"] - b["score"], 1)
    verdict = f"A scores {abs(d)} higher" if d > 0 else (f"B scores {abs(d)} higher" if d < 0 else "Tie")
    lines.append(f"  Verdict: {verdict}")
    only_a = [p for p in a["penalties"] if p not in b["penalties"]]
    only_b = [p for p in b["penalties"] if p not in a["penalties"]]
    if only_a:
        lines.append(f"  Only A has issues:")
        for p in only_a[:8]:
            lines.append(f"    ⚠️  {p}")
    if only_b:
        lines.append(f"  Only B has issues:")
        for p in only_b[:8]:
            lines.append(f"    ⚠️  {p}")
    lines.append(sep)
    lines.append("")
    print("\n".join(lines))


def run_batch(urls, timeout=15):
    """Pro: profile many URLs, print a summary table sorted by score."""
    rows = []
    errors = []
    for u in urls:
        try:
            p = _profile_url(u, timeout)
            rows.append((u, p["status"], p["score"], p["max_score"], p["grade"], len(p["penalties"])))
        except RuntimeError as e:
            errors.append((u, str(e)))
    rows.sort(key=lambda r: r[2], reverse=True)
    lines = []
    lines.append("")
    lines.append(f"  page-profile v{__version__} — BATCH (Pro): {len(rows)} ok, {len(errors)} failed")
    lines.append("  " + "─" * 76)
    lines.append(f"  {'URL':<48} {'HTTP':>4}  {'Score':>7}  {'Grade':>5}  Issues")
    for u, st, sc, mx, gr, n in rows:
        lines.append(f"  {u[:47]:<48} {st:>4}  {sc:>4}/{mx:<2}  {gr:>5}  {n}")
    for u, e in errors:
        lines.append(f"  {u[:47]:<48} FAIL  {e[:50]}")
    lines.append("  " + "─" * 76)
    if rows:
        avg = round(sum(r[2] for r in rows) / len(rows), 1)
        lines.append(f"  Average score: {avg}/{rows[0][3] if rows else MAX_WEIGHT}")
    lines.append("")
    print("\n".join(lines))
    if errors:
        sys.exit(1)


def _history_path():
    return os.path.join(os.path.expanduser("~"), ".page-profile-history.json")


def append_history(entry):
    try:
        hist = []
        if os.path.exists(_history_path()):
            with open(_history_path()) as f:
                hist = json.load(f)
        hist.append(entry)
        # keep last 500 entries — bounded storage, never grows unattended
        with open(_history_path(), "w") as f:
            json.dump(hist[-500:], f, ensure_ascii=False, indent=1)
    except (OSError, ValueError):
        pass  # history must never break a profile


def run_history(url=None):
    """Show how tracked pages changed over time."""
    try:
        with open(_history_path()) as f:
            hist = json.load(f)
    except (OSError, ValueError):
        print("No history yet. Profiles are recorded automatically when you run page-profile.")
        return
    if url:
        hist = [h for h in hist if h.get("url") == url]
    if not hist:
        print("No matching history entries.")
        return
    from collections import defaultdict
    by_url = defaultdict(list)
    for h in hist:
        by_url[h["url"]].append(h)
    for u, entries in by_url.items():
        print(f"\n{u}  ({len(entries)} snapshots)")
        prev = None
        for h in entries[-15:]:
            line = f"  {h['when']}  HTTP {h['status']:>3}  {h['score']:>5}/{h['max_score']}  {h['grade']}"
            delta = ""
            if prev is not None:
                d = round(h["score"] - prev, 1)
                delta = f"  ({'+' if d > 0 else ''}{d})"
            print(line + delta)
            prev = h["score"]
    print()


def run_html_report(p, out_path=None):
    """Client-ready single-file HTML report."""
    esc = lambda s: (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    r = p["result"]
    sec = r.get("security", {})
    og = r.get("og", {})
    checks = [
        ("Title", bool(r.get("title")), esc(r.get("title"))),
        ("Meta description", bool(r.get("meta_description")), esc(r.get("meta_description"))),
        ("Canonical", bool(r.get("canonical")), esc(r.get("canonical"))),
        ("Language", bool(r.get("language")), esc(r.get("language"))),
        ("Charset", bool(r.get("charset")), esc(r.get("charset"))),
        ("OG title", bool(og.get("title")), esc(og.get("title"))),
        ("OG description", bool(og.get("description")), esc(og.get("description"))),
        ("OG image", bool(og.get("image")), esc(og.get("image"))),
        ("JSON-LD", r.get("json_ld_count", 0) > 0, ", ".join(r.get("json_ld_types", [])[:6])),
        ("HSTS", sec.get("hsts"), ""),
        ("CSP", sec.get("csp"), ""),
        ("X-Frame-Options", sec.get("xfo"), ""),
        ("X-Content-Type-Options", sec.get("xcto"), ""),
        ("HTTPS", p["url"].startswith("https://"), ""),
    ]
    grade_colors = {"A": "#16a34a", "B": "#65a30d", "C": "#d97706", "D": "#ea580c", "F": "#dc2626"}
    gc = grade_colors.get(p["grade"], "#334155")
    rows = "".join(
        f"<tr><td>{esc(label)}</td><td style=\"color:{'#16a34a' if ok else '#dc2626'}\">"
        f"{'PASS' if ok else 'FAIL'}</td><td>{esc(detail)}</td></tr>"
        for label, ok, detail in checks
    )
    pens = "".join(f"<li>{esc(x)}</li>" for x in p["penalties"]) or "<li>None</li>"
    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page Profile Report — {esc(p['url'])}</title>
<style>
body{{font-family:-apple-system,'Segoe UI',sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;color:#0f172a;line-height:1.55}}
.badge{{display:inline-block;background:{gc};color:#fff;font-size:2.6rem;font-weight:700;border-radius:12px;padding:.4rem 1.1rem}}
table{{width:100%;border-collapse:collapse;margin:1.2rem 0}}
th,td{{text-align:left;padding:.5rem .7rem;border-bottom:1px solid #e2e8f0}}
th{{background:#f1f5f9}} code{{background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:.85em}}
footer{{color:#64748b;font-size:.85rem;margin-top:2rem;border-top:1px solid #e2e8f0;padding-top:1rem}}
</style></head><body>
<h1>Page Profile Report</h1>
<p><span class="badge">{p['grade']}</span> &nbsp; Score <strong>{p['score']}/{p['max_score']}</strong></p>
<p>URL: <code>{esc(p['url'])}</code><br>Status: HTTP {p['status']} · Generated {esc(__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'))}</p>
<table><tr><th>Check</th><th>Result</th><th>Detail</th></tr>{rows}</table>
<h2>Improvement points</h2><ul>{pens}</ul>
<footer>Generated with page-profile v{__version__} Pro · <a href="https://hermes-passiv.pages.dev/page-profile">hermes-passiv.pages.dev/page-profile</a></footer>
</body></html>"""
    path = out_path or "page-profile-report.html"
    with open(path, "w") as f:
        f.write(html_doc)
    print(f"HTML report written to {path}")


def activate(key):
    key = key.strip()
    if not validate_license_key(key):
        print("Error: that license key is not valid. Check it and try again.")
        sys.exit(2)
    try:
        with open(LICENSE_FILE, "w") as f:
            f.write(key)
        os.chmod(LICENSE_FILE, 0o600)
        print(f"Pro activated ✓  (stored in {LICENSE_FILE})")
    except OSError as e:
        print(f"Could not write license file: {e}")
        sys.exit(2)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="page-profile — Zero-dependency web page profiler",
    )
    parser.add_argument("url", nargs="?", help="URL to profile (e.g., https://example.com)")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of terminal report")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds (default: 15)")
    parser.add_argument("--version", action="version", version=f"page-profile v{__version__}")
    # Pro features
    parser.add_argument("--compare", metavar=("URL_A", "URL_B"), nargs=2,
                        help="(Pro) Compare two URLs side by side")
    parser.add_argument("--batch", nargs="+", metavar="URL",
                        help="(Pro) Profile multiple URLs and show a ranked table")
    parser.add_argument("--urls-from-file", metavar="FILE",
                        help="(Pro) File with one URL per line, used with --batch")
    parser.add_argument("--html-report", metavar="PATH", nargs="?", const="page-profile-report.html",
                        help="(Pro) Write a client-ready HTML report")
    parser.add_argument("--history", action="store_true",
                        help="Show how pages scored over previous runs (free)")
    parser.add_argument("--activate", metavar="KEY",
                        help="Activate a page-profile Pro license key")
    parser.add_argument("--gen-key", metavar="SEED",
                        help=argparse.SUPPRESS)  # seller-only helper

    args = parser.parse_args()

    if args.gen_key:
        print(make_license_key(args.gen_key))
        return

    if args.activate:
        activate(args.activate)
        return

    if args.history:
        run_history()
        return

    if args.urls_from_file:
        require_pro("batch mode from file")
        try:
            with open(args.urls_from_file) as f:
                file_urls = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
        except OSError as e:
            print(f"Error reading {args.urls_from_file}: {e}", file=sys.stderr)
            sys.exit(1)
        args.batch = (args.batch or []) + file_urls

    if args.compare:
        require_pro("compare mode")
        run_compare(args.compare[0], args.compare[1], timeout=args.timeout)
        return

    if args.batch:
        require_pro("batch mode")
        run_batch(args.batch, timeout=args.timeout)
        return

    if not args.url:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Free single-URL profile
    status_code, headers, html, redirect_chain = fetch_page(args.url, timeout=args.timeout)
    if status_code == 0:
        print(f"Error: {html}")
        sys.exit(1)

    result = analyze(args.url, html, headers)
    sc, max_sc, grade, penalties = score(result)

    append_history({
        "url": args.url, "when": __import__('datetime').datetime.utcnow().strftime("%Y-%m-%d"),
        "status": status_code, "score": sc, "max_score": max_sc, "grade": grade,
    })

    if args.html_report:
        require_pro("HTML report")
        p = {"url": args.url, "status": status_code, "redirects": redirect_chain,
             "result": result, "score": sc, "max_score": max_sc,
             "grade": grade, "penalties": penalties}
        run_html_report(p, args.html_report)

    if args.json:
        print(format_json(args.url, status_code, redirect_chain, result, sc, max_sc, grade, penalties))
    else:
        print(format_terminal(args.url, status_code, redirect_chain, result, sc, max_sc, grade, penalties))


if __name__ == "__main__":
    main()