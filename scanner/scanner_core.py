#!/usr/bin/env python3
"""
scanner_core.py — Universal EAA/WCAG compliance scanner core.

Platform-independent: takes raw HTML (from any CMS — WordPress, Shopify,
Webflow, Next.js, Squarespace, hand-written HTML) and returns a structured,
JSON-serialisable report. No network access, no CMS assumptions.

Checks implemented (WCAG 2.1 AA subset most relevant to the European
Accessibility Act):
  1.  Images missing alt text
  2.  Form inputs without labels
  3.  Buttons/links with no accessible text
  4.  Missing page title / lang attribute / viewport meta
  5.  Heading structure (no h1, skipped levels)
  6.  Inline styles / attributes suggesting fixed font sizes or low contrast risk
  7.  iframes without titles
  8.  Tables without headers
  9.  Links opening in new windows without warning
 10.  ARIA misuse (aria-hidden on focusable elements)
"""

import json
import re
import sys
from dataclasses import dataclass, field, asdict

try:
    from html.parser import HTMLParser
except ImportError:
    sys.exit("Python stdlib required")

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


@dataclass
class Finding:
    rule_id: str
    severity: str          # "error" | "warning" | "notice"
    message: str
    count: int = 1
    examples: list = field(default_factory=list)


class _Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.imgs_no_alt = []
        self.imgs_alt_ok = 0
        self.inputs_unlabeled = []      # inputs lacking associated label/aria-label
        self.labels_for = set()
        self.empty_links = []
        self.empty_buttons = []
        self.headings = []              # (level, text)
        self.iframes_no_title = []
        self.tables = []                # has header?
        self.target_blank = 0
        self.aria_hidden_focusable = []
        self.fixed_font_px = 0
        self.title_present = False
        self.lang_attr = None
        self.viewport_meta = False
        self.form_count = 0
        self._in_title = False
        # buttons/links with no accessible text
        self._in_button_text = []
        self._button_open = False
        self.buttons_empty = []
        self.links_no_text = 0
        self.target_blank_no_warning = []
        # duplicate ids (breaks label[for]/aria-labelledby)
        self.ids_seen = {}
        self.dup_ids = set()
        # inline color contrast risk: light gray text on white
        self.low_contrast_risk = []
        # inline color pairs for WCAG 1.4.3 contrast checking
        self.color_pairs = []          # list of (fg, bg, font_size_pt_or_px_is_large)
        self._style_stack = []         # inherited fg/bg from ancestors (inline styles only)
        self._link_text = []      # stack of text buffers per open <a>
        self._blank_stack = []    # parallel: True if that <a> is target=_blank
        # track aria-labelledby/describedby ids and label wrapping
        self._open_label = None
        self._label_text_chars = 0
        self._labelled_ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        aid = a.get("id")
        if aid and aid in self.ids_seen:
            self.dup_ids.add(aid)
        elif aid:
            self.ids_seen[aid] = tag
        if tag == "title":
            self._in_title = True
        elif tag == "html":
            self.lang_attr = a.get("lang")
        elif tag == "meta" and (a.get("name") or "").lower() == "viewport":
            self.viewport_meta = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = int(tag[1])
            self._heading_text = []
        elif tag == "img":
            alt = a.get("alt")
            if alt is None or alt.strip() == "":
                src = (a.get("src") or "")[:80]
                self.imgs_no_alt.append(src)
            else:
                self.imgs_alt_ok += 1
        elif tag == "button" or tag == "input" and \
                (a.get("type") or "").lower() in ("submit", "button"):
            if tag == "button":
                self._button_open = True
                self._in_button_text = []
        elif tag == "label":
            self._open_label = len(self.get_starttag_text() or "")
            if a.get("for"):
                self.labels_for.add(a["for"])
        elif tag == "input" or tag == "select" or tag == "textarea":
            itype = (a.get("type") or "text").lower()
            if itype in ("hidden", "submit", "button", "reset", "image"):
                return
            labelled = (
                aid and aid in self.labels_for or
                a.get("aria-label") or a.get("aria-labelledby") or
                a.get("title")
            )
            if not labelled:
                name = a.get("name") or a.get("placeholder") or ""
                self.inputs_unlabeled.append(f"{tag}[{itype}] {name}"[:60])
        elif tag == "a":
            self._blank_stack.append(a.get("target") == "_blank")
            self._link_text.append([])
        elif tag == "iframe":
            if not a.get("title"):
                self.iframes_no_title.append((a.get("src") or "")[:60])
        elif tag == "table":
            self.tables.append(False)   # assume no header until seen
        elif tag == "th":
            if self.tables:
                self.tables[-1] = True
        elif tag == "form":
            self.form_count += 1
        if a.get("aria-hidden") == "true" and any(
            k in a for k in ("tabindex",)) and a.get("tabindex") not in ("-1",):
            self.aria_hidden_focusable.append(tag)
        style = a.get("style") or ""
        if re.search(r"font-size\s*:\s*\d+px", style):
            self.fixed_font_px += 1
        # inline colour contrast (WCAG 1.4.3) — track inherited fg/bg
        parent = self._style_stack[-1] if self._style_stack else ("", "")
        fg = parent[0]
        bg = parent[1]
        m_fg = re.search(r"(?:^|;)\s*color\s*:\s*([^;!]+)", style)
        if m_fg:
            fg = m_fg.group(1).strip()
        m_bg = re.search(r"background(?:-color)?\s*:\s*([^;!]+)", style)
        if m_bg:
            bgv = m_bg.group(1).strip()
            # ignore gradients / url() backgrounds — can't compute a ratio
            if not re.search(r"url\(|gradient\(", bgv):
                bg = bgv
        large = bool(re.search(
            r"font-size\s*:\s*(?:1[89]\d*[.,]?|2\d+|[3-9]\d+)\s*px|"
            r"font-size\s*:\s*(?:14|1[5-9]|[2-9]\d+(?:\.\d+)?)pt|"
            r"font-weight\s*:\s*(?:bold|[6-9]00)", style))
        self._style_stack.append((fg, bg, large))

    def handle_endtag(self, tag):
        if self._style_stack:
            self._style_stack.pop()
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = "".join(self._heading_text).strip()
            self.headings.append((self._in_heading, text))
            self._in_heading = None
        elif tag == "label":
            self._open_label = None
        elif tag == "button" and self._button_open:
            self._button_open = False
            if not "".join(self._in_button_text).strip():
                self.buttons_empty.append("button")
        elif tag == "a" and self._link_text:
            buf = self._link_text.pop()
            is_blank = self._blank_stack.pop()
            text = "".join(buf).strip()
            if not text:
                self.links_no_text += 1
            elif is_blank and "new window" not in text.lower() \
                    and "new tab" not in text.lower():
                self.target_blank_no_warning.append(text[:50])

    def handle_data(self, data):
        if self._in_title and data.strip():
            self.title_present = True
        if getattr(self, "_in_heading", None):
            self._heading_text.append(data)
        if self._button_open:
            self._in_button_text.append(data)
        for buf in self._link_text:
            buf.append(data)
        # record colour pair when text is rendered with both fg and bg known
        if data.strip() and self._style_stack:
            st = self._style_stack[-1]
            if st[0] and st[1]:
                self.color_pairs.append((st[0], st[1], bool(st[2]), data.strip()[:40]))


# --- WCAG 1.4.3 contrast maths -------------------------------------------

def _parse_color(s: str):
    """Return (r, g, b) 0-255 floats or None if unparseable/transparent."""
    s = s.strip().lower()
    if s in ("transparent", "inherit", "currentcolor", "initial"):
        return None
    m = re.match(r"#([0-9a-f]{3})$", s)
    if m:
        r, g, b = m.group(1)
        return tuple(int(c * 2, 16) for c in (r, g, b))
    m = re.match(r"#([0-9a-f]{6})", s)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"rgba?\(([^)]+)\)", s)
    if m:
        parts = [p.strip() for p in m.group(1).split(",")]
        if len(parts) >= 4 and float(parts[3]) < 0.9:
            return None   # semi-transparent — can't determine effective colour
        try:
            vals = []
            for p in parts[:3]:
                if p.endswith("%"):
                    vals.append(float(p[:-1]) * 2.55)
                else:
                    vals.append(float(p))
            return tuple(vals)
        except ValueError:
            return None
    named = {
        "white": (255, 255, 255), "black": (0, 0, 0), "red": (255, 0, 0),
        "green": (0, 128, 0), "blue": (0, 0, 255), "gray": (128, 128, 128),
        "grey": (128, 128, 128), "silver": (192, 192, 192),
        "yellow": (255, 255, 0), "orange": (255, 165, 0), "navy": (0, 0, 128),
        "teal": (0, 128, 128), "purple": (128, 0, 128), "maroon": (128, 0, 0),
        "olive": (128, 128, 0), "lime": (0, 255, 0), "aqua": (0, 255, 255),
        "cyan": (0, 255, 255), "fuchsia": (255, 0, 255), "magenta": (255, 0, 255),
    }
    return named.get(s)


def _rel_lum(rgb) -> float:
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg, bg):
    """WCAG 1.4.3 contrast ratio, or None if a colour can't be parsed."""
    f, b = _parse_color(fg), _parse_color(bg)
    if not f or not b:
        return None
    lf, lb = _rel_lum(f), _rel_lum(b)
    hi, lo = max(lf, lb), min(lf, lb)
    return (hi + 0.05) / (lo + 0.05)


def scan_html(html: str) -> dict:
    """Scan an HTML string; return report dict."""
    c = _Collector()
    findings = []
    try:
        c.feed(html)
    except Exception as e:
        return {"ok": False, "error": f"parse error: {e}", "score": None,
                "findings": [], "summary": {}}
    c.close()

    def add(rid, sev, msg, items=None):
        n = len(items) if items is not None else 0
        if n:
            findings.append(Finding(
                rid, sev, msg.format(n=n), n, [str(i)[:80] for i in items[:3]]))

    add("IMG_ALT", "error",
        "{n} image(s) missing alt text", c.imgs_no_alt)
    add("FORM_LABEL", "error",
        "{n} form field(s) without an associated label", c.inputs_unlabeled)
    add("LINK_TEXT", "error",
        "{n} link(s) with no accessible text",
        ["link" for _ in range(c.links_no_text)])
    add("BUTTON_TEXT", "error",
        "{n} button(s) with no accessible text", c.buttons_empty)
    add("TARGET_BLANK", "warning",
        "{n} link(s) opening in a new window without warning the user",
        c.target_blank_no_warning)
    add("DUP_ID", "error",
        "{n} duplicate id attribute value(s) "
        "(breaks label/aria references)", sorted(c.dup_ids))
    add("IFRAME_TITLE", "warning",
        "{n} iframe(s) without a title attribute", c.iframes_no_title)
    for i, has_header in enumerate(c.tables):
        if not has_header:
            findings.append(Finding(
                "TABLE_HEADER", "warning",
                f"table #{i + 1} has no <th> header cells", 1))
    if not c.title_present:
        findings.append(Finding("DOC_TITLE", "error",
                                "page has no non-empty <title>", 1))
    if not c.lang_attr:
        findings.append(Finding("HTML_LANG", "error",
                                "<html> lacks a lang attribute", 1))
    if not c.viewport_meta:
        findings.append(Finding("VIEWPORT", "warning",
                                "missing viewport meta (zoom disabled/unresponsive)", 1))
    levels = [lvl for lvl, _ in c.headings]
    h1_count = sum(1 for lvl, _ in c.headings if lvl == 1)
    # heading level skips (e.g. h2 -> h4)
    skips = sum(1 for a_, b_ in zip(levels, levels[1:]) if b_ > a_ + 1)
    if h1_count == 0:
        findings.append(Finding("HEADING_H1", "warning",
                                "no <h1> found on the page", 1))
    if skips:
        findings.append(Finding("HEADING_SKIP", "warning",
                                f"{skips} heading level skip(s) "
                                "(e.g. h2 followed by h4)", skips))
    if c.fixed_font_px >= 3:
        findings.append(Finding("FIXED_PX_FONTS", "notice",
                                f"{c.fixed_font_px} inline fixed px font-sizes "
                                "(may block user zoom/text resize)", c.fixed_font_px))
    if c.aria_hidden_focusable:
        add("ARIA_HIDDEN_FOCUS", "error",
            "{n} element(s) with aria-hidden=true that are focusable",
            c.aria_hidden_focusable)
    # WCAG 1.4.3 contrast on inline-styled text
    low = []
    seen_pairs = set()
    for fg, bg, large, txt in c.color_pairs:
        ratio = contrast_ratio(fg, bg)
        if ratio is None:
            continue
        threshold = 3.0 if large else 4.5
        key = (fg, bg, large)
        if ratio < threshold and key not in seen_pairs:
            seen_pairs.add(key)
            low.append(f"{fg} on {bg}: {ratio:.2f}:1 (\"{txt}\")")
    if low:
        findings.append(Finding(
            "CONTRAST", "error",
            f"{len(low)} text colour combination(s) below the WCAG AA "
            "contrast minimum (4.5:1 normal text, 3:1 large text)",
            len(low), low[:3]))

    errors = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    notices = sum(1 for f in findings if f.severity == "notice")
    score = max(0, 100 - errors * 12 - warnings * 5 - notices * 2)

    return {
        "ok": True,
        "standard": "EAA / WCAG 2.1 AA (subset)",
        "score": score,
        "grade": ("A" if score >= 90 else "B" if score >= 75
                  else "C" if score >= 55 else "D"),
        "findings": [asdict(f) for f in sorted(
            findings, key=lambda f: ("error warning notice".split().index(f.severity)))],
        "summary": {
            "errors": errors, "warnings": warnings, "notices": notices,
            "images_checked": c.imgs_no_alt.__len__() + c.imgs_alt_ok,
            "tables": len(c.tables), "forms": c.form_count,
        },
    }


def scan_url(url: str, timeout: int = 15) -> dict:
    """Fetch a URL over HTTP(S) and scan the returned HTML."""
    import urllib.request
    import urllib.error

    def _open(u):
        rq = urllib.request.Request(
            u, headers={"User-Agent": "EAA-ComplianceScanner/1.0 (+site audit)"})
        try:
            return urllib.request.urlopen(rq, timeout=timeout)
        except urllib.error.HTTPError as e:
            # 3xx/4xx arrive as exceptions; 308 etc. still carry the body/headers
            return e

    r = _open(url)
    # follow up to 5 redirects manually (urllib does not retry body on 308)
    html = ""
    for _ in range(5):
        with r:
            if r.status in (301, 302, 303, 307, 308):
                from urllib.parse import urljoin
                url = urljoin(url, r.headers.get("Location") or "") or url
                r = _open(url)
                continue
            html = r.read(2_000_000).decode(
                r.headers.get_content_charset() or "utf-8", errors="replace")
        break
    rep = scan_html(html)
    rep["url"] = url
    rep["html"] = html   # retained so crawl_site can extract same-origin links
    return rep


# --- link extraction + site crawl -------------------------------------------

_SKIP_HREF = re.compile(
    r"^(mailto:|tel:|javascript:|data:|#)", re.IGNORECASE)
_SKIP_EXT = re.compile(
    r"\.(zip|tar|gz|tgz|pdf|png|jpe?g|gif|svg|webp|ico|css|js|json|xml|"
    r"woff2?|mp4|mp3|dmg|exe|deb|appimage|whl)(\?|$)", re.IGNORECASE)
_HREF_RE = re.compile(r"""<a\s[^>]*href\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.IGNORECASE)


def extract_links(html: str, base_url: str) -> list:
    """Same-origin <a href> links found in *html*, absolute and deduplicated."""
    from urllib.parse import urljoin, urlsplit
    parts = urlsplit(base_url)
    out = set()
    for m in _HREF_RE.finditer(html):
        href = (m.group(1) or m.group(2) or "").strip()
        if not href or _SKIP_HREF.match(href) or _SKIP_EXT.search(href):
            continue
        u = urljoin(base_url, href)
        p = urlsplit(u)
        if p.scheme not in ("http", "https") or p.netloc != parts.netloc:
            continue          # same-site only; malformed URLs fail urljoin/split harmlessly
        out.add(u.split("#", 1)[0])
    return sorted(out)


def crawl_site(start_url: str, max_pages: int = 10, timeout: int = 15,
               delay_s: float = 0.25, on_page=None) -> dict:
    """BFS-crawl same-origin links from *start_url* up to *max_pages* pages.

    Returns {"pages": [report,...], "aggregate": {...}}. Individual page
    failures are reported in the result, never raised.
    """
    import time

    seen = set()
    queue = [start_url]
    pages = []
    while queue and len(seen) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            rep = scan_url(url, timeout=timeout)
        except Exception as e:
            rep = {"ok": False, "error": str(e), "score": None,
                   "findings": [], "summary": {}}
        rep["target"] = url
        if not rep.get("ok"):
            # retry once on transient network hiccups
            try:
                time.sleep(delay_s)
                rep = scan_url(url, timeout=timeout)
                rep["target"] = url
            except Exception as e:
                rep = {"ok": False, "error": str(e), "score": None,
                       "findings": [], "summary": {}, "target": url}
        html = rep.get("html") or ""
        rep.pop("html", None)          # keep the aggregate report lean
        pages.append(rep)
        if on_page:
            try:
                on_page(rep, len(seen), max_pages)
            except Exception:
                pass
        if rep.get("ok"):
            queue.extend(link for link in extract_links(html, url)
                         if link not in seen)
        time.sleep(delay_s)

    ok_pages = [p for p in pages if p.get("ok")]
    totals = {"errors": 0, "warnings": 0, "notices": 0}
    by_rule = {}
    for p in ok_pages:
        s = p.get("summary", {})
        for k in totals:
            totals[k] += s.get(k, 0)
        for f in p["findings"]:
            by_rule[f["rule_id"]] = by_rule.get(f["rule_id"], 0) + f["count"]
    failed = len(pages) - len(ok_pages)
    avg_score = (round(sum(p["score"] for p in ok_pages) / len(ok_pages))
                 if ok_pages else None)
    worst = min(ok_pages, key=lambda p: p["score"]) if ok_pages else None
    aggregate = {
        "pagesScanned": len(pages),
        "pagesFailed": failed,
        "averageScore": avg_score,
        "grade": None if avg_score is None else
            ("A" if avg_score >= 90 else "B" if avg_score >= 75
             else "C" if avg_score >= 55 else "D"),
        "totalErrors": totals["errors"],
        "totalWarnings": totals["warnings"],
        "totalNotices": totals["notices"],
        "rulesByFrequency": sorted(by_rule.items(), key=lambda kv: -kv[1]),
        "worstPage": None if worst is None else
            {"target": worst.get("target"), "score": worst["score"]},
    }
    return {"pages": pages, "aggregate": aggregate}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: scanner_core.py <url-or-htmlfile>")
        sys.exit(2)
    arg = sys.argv[1]
    if arg.startswith("http"):
        print(json.dumps(scan_url(arg), indent=2))
    else:
        print(json.dumps(scan_html(open(arg).read()), indent=2))
