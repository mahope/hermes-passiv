"""Per-page normalisation used by build_sites.py.

Two passes over every HTML page in a dist:
  normalize_body  - strip page CSS that collides with the design system, map hard-coded
                    style="" values to classes/tokens, wrap tables, demote extra <h1>,
                    make sure there is exactly one <main id="main">.
  normalize_head  - rebuild the SEO block: title/description lengths, canonical, hreflang
                    (both ways), Open Graph, Twitter, icons, manifest, fonts, JSON-LD.

Everything is regex-based on purpose: the pages are hand-written static HTML and a
real parser would re-serialise them differently.
"""
from __future__ import annotations

import html as htmllib
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
CSS_VERSION = hashlib.sha1((_ROOT / 'site' / 'style.css').read_bytes()).hexdigest()[:8]
SHELL_VERSION = hashlib.sha1((_ROOT / 'site' / 'shell.js').read_bytes()).hexdigest()[:8]
# Google Fonts per product identity (display=swap is in the query string).
FONTS = {
    "Clean Copy": "family=Inter:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,500;6..72,600",
    "DeskUptime": "family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500",
    "BugBottle": "family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600",
}
FONTS_DEFAULT = "family=Inter:wght@400;500;600;700"
THEME_SCRIPT = ("<script>(function(){var d=document.documentElement;d.classList.add('has-js');"
                "try{var t=localStorage.getItem('theme');if(t==='light'||t==='dark')d.setAttribute('data-theme',t)}catch(e){}})();</script>")

# ---------------------------------------------------------------------------
# Body
# ---------------------------------------------------------------------------

# Selectors the design system owns. Page-level rules for these are dropped.
OWNED_SELECTORS = {
    "*", "html", "body", "main", "header", "footer", "footer a", "footer p", "nav", "section", "h1", "h2", "h3", "h4", "p", "a",
    "a:hover", "ul", "ol", "li", "code", "pre", "pre code", "kbd", "table", "th", "td", "tr", "img", "hr", "blockquote", "details",
    "summary", "label", "legend", "fieldset", "button", "input", "select", "textarea", "input[type=text]", "input[type=url]",
    ".container", ".card", ".card h3", ".card p", ".cards", ".btn", ".btn-primary", ".btn-primary:hover", ".btn-secondary",
    ".btn-secondary:hover", ".btn-small", ".badge", ".hero", ".hero h1", ".hero p", ".subtitle", ".tagline", ".lead",
    ".hero-cta", ".hero-note", ".compare", ".compare th", ".compare td", ".compare tr", "pre.cmd", "pre.cmd code", ".cmd",
    ".breadcrumb", ".breadcrumb a", ".breadcrumb a:hover", ".breadcrumb span", ".book-header", ".book-header h1",
    ".book-header .tagline", ".chapter-list", ".chapter-list ul", ".chapter-list li", ".cta-section", ".cta-section h2",
    ".free-note", ".sr-only", ".hint", ".actions", ".price", ".dl-card", ".tagchip", ".tag", ".related-guides",
    ".related-books", ".book-cta", ".cta-scan", ".notice", ".book-card", ".book-card img", ".book-card-body", ".book-card-meta",
    ".plat-card", ".plat-card h2", ".plat-card p", ".plat-links", ".plat-links a", ".plat-icon", ".hubcard", ".hubcard h3",
    ".hubcard p", ".problem-cards", ".faq-item", ".faq-item h3", ".faq-item p", "details.faq", "details.faq summary",
    "details.faq p", ".site-footer", ".site-header", ".skip-link", ".muted", ".term", ".cli-demo", ".feature-list",
    ".pricing", ".tier-card", ".tier-card.pro", ".tier-card ul", ".two-col", ".prose", ".meta", ".author", ".output",
    ".pass", ".fail", ".warn", ".sev-ok", ".sev-error", ".sev-warning", ".grade-A", ".grade-B", ".grade-C", ".grade-D",
    ".gen", ".gen fieldset", ".gen legend", ".gen label", ".gen textarea", ".gen select", ".gen input[type=text]",
    ".gen input[type=email]", ".gen input[type=url]", ".privacy-note", ".jf-wrap", ".input-group input", ".input-group button",
    ":root",
}
# Prefixes: any selector starting with one of these is dropped too.
OWNED_PREFIXES = (".site-header", ".site-footer", ".site-nav", ".lang-switch", ".nav-toggle", ".skip-link", ".family-bar",
                  ".crumbs", ".toc", ".prose-layout", ".prose-aside", ".search-", ".btt", ".copy-btn", ".prev-next", ".bb-live",
                  ".layout-wide", ".article-meta", ".header-tools", ".theme-btn")
# Page-level layout wrappers (main.jf-wrap { max-width: 1100px; … }): the shell owns the width now.
WRAP_SELECTOR_RE = re.compile(r"^(?:main|div)?\.(?:[\w-]+-)?wrap$")

# Exact style="" values -> class names (the value is removed from the element).
STYLE_TO_CLASS = {
    "color:#555;font-size:14px;": "muted small",
    "color:#555;font-size:14px": "muted small",
    "margin:12px 0 0;font-size:13px;color:#555;": "muted small mt-1",
    "margin:8px 0 12px;font-size:14px;color:#374151;": "muted small",
    "color:var(--color-text-muted);font-size:0.88rem": "muted small",
    "font-size:0.75em;display:inline-block;margin-bottom:6px;": "badge",
    "text-align:center;margin-top:16px;": "text-center mt-1",
    "text-align:center;margin-top:24px;": "text-center mt-1-5",
    "text-align:center;margin-top:20px;": "text-center mt-1-5",
    "text-align:center;": "text-center",
    "margin-top:0;": "mt-0",
    "margin-top:0": "mt-0",
    "list-style:none;padding:0;margin:0;": "list-plain",
    "border:1px solid #ddd;border-radius:8px;padding:16px 20px;margin:32px 0;": "",
    "border:1px solid #e5e7eb;border-radius:10px;padding:20px 24px;margin:32px 0;": "",
    "background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:18px 22px;margin:28px 0;": "",
    "background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:18px 22px;margin:28px 0;": "",
    "color:#1d4ed8;font-weight:600;text-decoration:none;": "tool-link",
    "color:var(--color-accent);font-weight:600;text-decoration:none;font-size:1.02rem": "tool-link",
    "color:var(--color-accent);text-decoration:none;": "tool-link",
    "color:var(--color-accent);text-decoration:none": "tool-link",
    "padding:32px 24px;": "",
    "padding:48px 0 40px": "",
    "margin:2.5rem 0;": "",
    "display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1rem;": "",
    "border:1px solid var(--color-border);border-radius:12px;padding:22px;background:var(--color-surface)": "card",
    "padding:16px 20px;background:var(--color-surface-2);border:1px solid var(--color-border);border-radius:var(--radius);font-size:0.95rem;": "notice",
}
# Hard-coded colours inside remaining style="" values -> tokens.
STYLE_COLOR_MAP = [
    (re.compile(r"#(?:555|555555|374151|4b5563|6b7280|666|667|777|888|64748b|94a3b8|5a6b78)\b", re.I), "var(--color-text-muted)"),
    (re.compile(r"#(?:0f172a|0d1117|1e293b)\b", re.I), "var(--color-code-bg)"),
    (re.compile(r"#(?:e6edf3|e2e8f0|f1f5f9)\b(?=[^;]*$)", re.I), "var(--color-code-text)"),
    (re.compile(r"#(?:15803d|157a3c|16a34a|166534)\b", re.I), "var(--color-green)"),
    (re.compile(r"#(?:0b6e8f|38bdf8|0369a1)\b", re.I), "var(--color-accent)"),
    (re.compile(r"#(?:a35a10|b45309)\b", re.I), "var(--color-orange)"),
    (re.compile(r"#(?:a31515|b91c1c|dc2626)\b", re.I), "var(--color-red)"),
    (re.compile(r"#(?:f5f7fa|eef3f8|eef3f7)\b", re.I), "var(--color-surface-2)"),
    (re.compile(r"#(?:ddd|dddddd|e5e7eb|e2e8f0|bfdbfe|bbf7d0|ccc|eee)\b", re.I), "var(--color-border)"),
    (re.compile(r"#(?:eff6ff|f0fdf4|f8fafc|f9fafb|f3f4f6|f5f5f5|fafafa)\b", re.I), "var(--color-surface-2)"),
    (re.compile(r"#(?:1d4ed8|2563eb|1e40af|5b8def)\b", re.I), "var(--color-accent)"),
    (re.compile(r"#(?:111|111827|1f2937|222|333|000)\b", re.I), "var(--color-text)"),
    (re.compile(r"#(?:fff|ffffff)\b", re.I), "var(--color-surface)"),
    (re.compile(r"border-radius:\s*(?:8|10|12|14|16)px", re.I), "border-radius:var(--radius)"),
]

STYLE_BLOCK_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
STYLE_ATTR_RE = re.compile(r"""<([a-zA-Z][\w-]*)([^>]*?)\sstyle="([^"]*)"([^>]*)>""")
CLASS_ATTR_RE = re.compile(r'\sclass="([^"]*)"')
TABLE_RE = re.compile(r"<table\b[^>]*>.*?</table>", re.S | re.I)
H1_RE = re.compile(r"<h1\b([^>]*)>(.*?)</h1>", re.S | re.I)


def _split_rules(css: str):
    """Yield (prelude, body, is_block) for a flat CSS string, handling nested @media."""
    i, n = 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            yield css[i:], "", False
            return
        prelude = css[i:j]
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == "{":
                depth += 1
            elif css[k] == "}":
                depth -= 1
            k += 1
        yield prelude, css[j + 1:k - 1], True
        i = k


def _norm_sel(s: str) -> str:
    s = re.sub(r"\s+", " ", s.strip())
    s = s.replace('"', "").replace("'", "")
    return s


def _owned(selector: str) -> bool:
    s = _norm_sel(selector)
    if s in OWNED_SELECTORS or s.startswith(OWNED_PREFIXES) or WRAP_SELECTOR_RE.match(s):
        return True
    # ".compare th, .compare td" style lists: owned only if every part is owned
    return False


def scrub_css(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    for prelude, body, is_block in _split_rules(css):
        p = prelude.strip()
        if not is_block:
            if p:
                out.append(p)
            continue
        if p.startswith("@media") or p.startswith("@supports"):
            inner = scrub_css(body)
            if inner.strip():
                out.append(f"{p} {{ {inner} }}")
            continue
        if p.startswith("@"):  # keyframes, font-face: keep
            out.append(f"{p} {{{body}}}")
            continue
        keep = [s for s in p.split(",") if s.strip() and not _owned(s)]
        if not keep:
            continue
        body = re.sub(r"\s+", " ", body).strip()
        out.append(f"{', '.join(s.strip() for s in keep)} {{ {body} }}")
    return "\n".join(out)


HEX_DECL_RE = re.compile(r"(background(?:-color)?|color|border(?:-color|-top|-bottom|-left|-right)?)\s*:\s*([^;]*?)#([0-9a-fA-F]{3,8})\b")


def _lum(hex6: str) -> float:
    h = hex6[:6] if len(hex6) >= 6 else "".join(c * 2 for c in hex6[:3])
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _hex_to_token(m: re.Match) -> str:
    prop, pre, hx = m.group(1), m.group(2), m.group(3)
    l = _lum(hx)
    if prop.startswith("border"):
        tok = "var(--color-border)"
    elif prop.startswith("background"):
        tok = "var(--color-surface-2)" if l > 0.6 else "var(--color-code-bg)"
    else:
        tok = "var(--color-code-text)" if l > 0.7 else "var(--color-text-muted)" if l > 0.25 else "var(--color-text)"
    return f"{prop}:{pre}{tok}"


def _apply_style_attr(m: re.Match) -> str:
    tag, before, value, after = m.group(1), m.group(2), m.group(3).strip(), m.group(4)
    key = value if value in STYLE_TO_CLASS else value.rstrip(";") + ";"
    if key in STYLE_TO_CLASS or value in STYLE_TO_CLASS:
        cls = STYLE_TO_CLASS.get(value, STYLE_TO_CLASS.get(key, ""))
        attrs = before + after
        if cls:
            cm = CLASS_ATTR_RE.search(attrs)
            if cm:
                existing = cm.group(1).split()
                merged = existing + [c for c in cls.split() if c not in existing]
                attrs = attrs[: cm.start()] + f' class="{" ".join(merged)}"' + attrs[cm.end():]
            else:
                attrs = f' class="{cls}"' + attrs
        return f"<{tag}{attrs}>"
    new = value
    for rx, rep in STYLE_COLOR_MAP:
        new = rx.sub(rep, new)
    new = HEX_DECL_RE.sub(_hex_to_token, new)
    if tag.lower() not in ("img", "svg", "td", "th", "col"):
        new = re.sub(r"max-width\s*:[^;]*;?", "", new).strip()
    if not new:
        return f"<{tag}{before}{after}>"
    return f'<{tag}{before} style="{new}"{after}>'


def _wrap_tables(text: str) -> str:
    def sub(m: re.Match) -> str:
        start = m.start()
        # already wrapped? look back a little for an open .table-wrap
        back = text[max(0, start - 200): start]
        if re.search(r'class="[^"]*table-wrap[^"]*"[^>]*>\s*$', back):
            return m.group(0)
        return '<div class="table-wrap">' + m.group(0) + "</div>"
    return TABLE_RE.sub(sub, text)


SCRIPT_SPLIT_RE = re.compile(r"(<script\b.*?</script>|<pre\b.*?</pre>|<textarea\b.*?</textarea>)", re.S | re.I)
H1_TAG_RE = re.compile(r"<h1\b([^<>]*)>(.*?)</h1>", re.S | re.I)


def _demote_extra_h1(text: str) -> str:
    """Keep the first real <h1> in <body>; turn the rest into <h2>. Skips script/pre/textarea."""
    bm = re.search(r"<body[^>]*>", text, re.I)
    if not bm:
        return text
    head, body = text[: bm.end()], text[bm.end():]
    seen = [False]

    def sub(m: re.Match) -> str:
        if not seen[0]:
            seen[0] = True
            return m.group(0)
        return f"<h2{m.group(1)}>{m.group(2)}</h2>"
    parts = SCRIPT_SPLIT_RE.split(body)
    for i in range(0, len(parts), 2):
        parts[i] = H1_TAG_RE.sub(sub, parts[i])
    return head + "".join(parts)


def normalize_body(text: str) -> str:
    # 1. page CSS: drop rules for selectors owned by the design system
    def style_sub(m: re.Match) -> str:
        css = scrub_css(m.group(1))
        return f"<style>\n{css}\n</style>" if css.strip() else ""
    text = STYLE_BLOCK_RE.sub(style_sub, text)
    # 2. inline style attributes
    text = STYLE_ATTR_RE.sub(_apply_style_attr, text)
    # 3. tables scroll inside their own box
    text = _wrap_tables(text)
    # 4. one h1 per page
    text = _demote_extra_h1(text)
    # 5. legacy relative stylesheet references
    text = re.sub(r'<link[^>]+href="(?:\./)?(?:styles?\.css)"[^>]*>\s*', "", text)
    text = re.sub(r'<link[^>]+href="/assets/site\.css"[^>]*>\s*', "", text)
    # 6. old google fonts links (re-added once by the head pass)
    text = re.sub(r'<link[^>]+fonts\.g(?:oogleapis|static)\.com[^>]*>\s*', "", text)
    return text


# ---------------------------------------------------------------------------
# Head
# ---------------------------------------------------------------------------
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
DESC_RE = re.compile(r'<meta\s+name="description"\s+content="([^"]*)"\s*/?>', re.I)
DESC_RE2 = re.compile(r'<meta\s+content="([^"]*)"\s+name="description"\s*/?>', re.I)
OG_RE = re.compile(r'<meta\s+(?:property|name)="(og:[\w:]+|twitter:[\w:]+)"\s+content="([^"]*)"\s*/?>', re.I)
LDJSON_RE = re.compile(r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
STRIP_HEAD_RE = [
    re.compile(r'\s*<meta\s+name="description"[^>]*>', re.I),
    re.compile(r'\s*<meta\s+content="[^"]*"\s+name="description"[^>]*>', re.I),
    re.compile(r'\s*<link\s+rel="canonical"[^>]*>', re.I),
    re.compile(r'\s*<link\s+rel="alternate"[^>]*hreflang[^>]*>', re.I),
    re.compile(r'\s*<meta\s+(?:property|name)="(?:og|twitter):[^"]*"[^>]*>', re.I),
    re.compile(r'\s*<link\s+rel="(?:icon|shortcut icon|apple-touch-icon|manifest|sitemap|preconnect)"[^>]*>', re.I),
    re.compile(r'\s*<meta\s+name="theme-color"[^>]*>', re.I),
    re.compile(r'\s*<meta\s+name="author"[^>]*>', re.I),
    re.compile(r'\s*<link\s+rel="stylesheet"\s+href="/style\.css"[^>]*>', re.I),
]
TITLE_SUFFIX_RE = re.compile(r"\s*[|·—–-]\s*(mahoje\.dk|mahope\.tools|Hermes Passiv|Hermes Compliance Tools|Mahope)\s*$", re.I)
TITLE_PAREN_RE = re.compile(r"\s*\((?:Guide|Updated)?\s*20\d\d\)\s*$", re.I)


def clamp_title(t: str, limit: int = 60) -> str:
    t = htmllib.unescape(re.sub(r"\s+", " ", t)).strip()
    if len(t) <= limit:
        return t
    t = TITLE_SUFFIX_RE.sub("", t)
    t = TITLE_PAREN_RE.sub("", t)
    if len(t) <= limit:
        return t
    for sep in (" — ", " – ", " | ", ": ", " - "):
        if sep in t:
            head = t.split(sep, 1)[0].strip()
            if 40 <= len(head) <= limit:
                return head
    cut = t[:limit]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:—–-")


def clamp_desc(d: str, limit: int = 160) -> str:
    d = htmllib.unescape(re.sub(r"\s+", " ", d)).strip()
    if len(d) <= limit:
        return d
    head = d[:limit]
    m = list(re.finditer(r"[.!?](?=\s|$)", head))
    if m and m[-1].end() >= 70:
        return head[: m[-1].end()]
    cut = head[: limit - 1]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,;:—–-") + "…"


def esc(s: str) -> str:
    return htmllib.escape(s, quote=True)


def page_kind(dest: str) -> str:
    if dest in ("index.html", "da/index.html"):
        return "home"
    if "/blog/" in "/" + dest or dest.startswith("blog/"):
        return "article"
    if dest.startswith("books/") or dest.startswith("da/books/"):
        return "book"
    if dest.startswith("guides/"):
        return "guide"
    return "page"


def _ld_types(blocks: list[str]) -> set[str]:
    types: set[str] = set()
    for b in blocks:
        for m in re.finditer(r'"@type"\s*:\s*"([A-Za-z]+)"', b):
            types.add(m.group(1))
    return types


def _fix_article_dates(block: str, published: str, modified: str) -> str:
    """Add datePublished/dateModified to an existing Article block if missing."""
    try:
        data = json.loads(block)
    except (json.JSONDecodeError, ValueError):
        return block

    def patch(obj):
        if isinstance(obj, dict):
            t = obj.get("@type")
            if t in ("Article", "BlogPosting", "TechArticle", "NewsArticle"):
                obj.setdefault("datePublished", published)
                obj.setdefault("dateModified", modified)
            for v in obj.values():
                patch(v)
        elif isinstance(obj, list):
            for v in obj:
                patch(v)
    patch(data)
    return json.dumps(data, ensure_ascii=False)


PERSON = {"@type": "Person", "name": "Mads Holst Jensen", "url": "https://mahoje.dk"}


def build_head(*, site_url: str, brand: dict, lang: str, dest: str, canonical: str, alternates: dict[str, str],
               title: str, description: str, og_image: str, og_type: str, existing_ld: list[str],
               dates: tuple[str, str] | None, github: str, kind: str | None = None) -> tuple[str, str, str]:
    """Return (new_title, new_description, head_html)."""
    t = clamp_title(title)
    d = clamp_desc(description)
    accent = brand["accent"]
    name = brand["name"]
    lines = [
        f'<meta name="description" content="{esc(d)}">',
        '<meta name="author" content="Mads Holst Jensen">',
        f'<link rel="canonical" href="{canonical}">',
    ]
    if alternates:
        for code in ("en", "da"):
            if code in alternates:
                lines.append(f'<link rel="alternate" hreflang="{code}" href="{alternates[code]}">')
        xdef = alternates.get("en") or alternates.get(lang) or canonical
        lines.append(f'<link rel="alternate" hreflang="x-default" href="{xdef}">')
    lines += [
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:site_name" content="{esc(name)}">',
        f'<meta property="og:locale" content="{"da_DK" if lang == "da" else "en_US"}">',
        f'<meta property="og:title" content="{esc(t)}">',
        f'<meta property="og:description" content="{esc(d)}">',
        f'<meta property="og:url" content="{canonical}">',
        f'<meta property="og:image" content="{og_image}">',
        f'<meta property="og:image:alt" content="{esc(name)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(t)}">',
        f'<meta name="twitter:description" content="{esc(d)}">',
        f'<meta name="twitter:image" content="{og_image}">',
        f'<meta name="theme-color" content="{accent}">',
        '<link rel="icon" href="/favicon.ico" sizes="32x32">',
        '<link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">',
        '<link rel="manifest" href="/site.webmanifest">',
        '<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">',
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{FONTS.get(name, FONTS_DEFAULT)}&display=swap">',
        THEME_SCRIPT,
        f'<link rel="stylesheet" href="/style.css?v={CSS_VERSION}">',
    ]
    if og_image.endswith("/og.png") or og_image.endswith("/og-da.png"):
        lines.insert(lines.index(f'<meta property="og:image:alt" content="{esc(name)}">'),
                     '<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">')

    # JSON-LD
    kind = kind or page_kind(dest)
    types = _ld_types(existing_ld)
    ld_blocks = []
    if kind == "home":
        if "WebSite" not in types:
            ld_blocks.append({"@context": "https://schema.org", "@type": "WebSite", "name": name, "url": site_url + "/",
                              "inLanguage": lang, "author": PERSON, "publisher": {"@type": "Organization", "name": "mahoje.dk",
                              "url": "https://mahoje.dk", "founder": PERSON}})
        if "Organization" not in types:
            ld_blocks.append({"@context": "https://schema.org", "@type": "Organization", "name": "mahoje.dk",
                              "url": "https://mahoje.dk", "logo": site_url + "/icon-512.png", "founder": PERSON,
                              "sameAs": [github]})
        if brand.get("install") and "SoftwareApplication" not in types:
            ld_blocks.append({"@context": "https://schema.org", "@type": "SoftwareApplication", "name": name,
                              "url": site_url + "/", "applicationCategory": "DeveloperApplication",
                              "operatingSystem": "Windows, macOS, Linux", "author": PERSON, "license": "https://opensource.org/license/mit",
                              "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "codeRepository": github})
    elif kind in ("article", "guide") and dates:
        if not types & {"Article", "BlogPosting", "TechArticle", "NewsArticle"}:
            ld_blocks.append({"@context": "https://schema.org", "@type": "Article", "headline": t, "description": d,
                              "inLanguage": lang, "datePublished": dates[0], "dateModified": dates[1], "author": PERSON,
                              "publisher": {"@type": "Organization", "name": "mahoje.dk", "url": "https://mahoje.dk",
                                            "logo": {"@type": "ImageObject", "url": site_url + "/icon-512.png"}},
                              "image": og_image, "mainEntityOfPage": canonical})
    if not existing_ld and not ld_blocks:
        ld_blocks.append({"@context": "https://schema.org", "@type": "WebPage", "name": t, "description": d, "url": canonical,
                          "inLanguage": lang, "isPartOf": {"@type": "WebSite", "name": name, "url": site_url + "/"},
                          "author": PERSON})
    for b in ld_blocks:
        lines.append('<script type="application/ld+json">' + json.dumps(b, ensure_ascii=False) + "</script>")
    return t, d, "\n".join(lines)


def normalize_head(text: str, **kw) -> tuple[str, dict]:
    """Rewrite <head>. kw is passed to build_head minus title/description/existing_ld which come from the page."""
    head_end = re.search(r"</head>", text, re.I)
    if not head_end:
        return text, {}
    head = text[: head_end.start()]
    body = text[head_end.start():]
    tm = TITLE_RE.search(head)
    title = tm.group(1) if tm else kw["brand"]["name"]
    dm = DESC_RE.search(head) or DESC_RE2.search(head)
    desc = dm.group(1) if dm else ""
    ogs = dict((k.lower(), v) for k, v in OG_RE.findall(head))
    if not desc:
        desc = ogs.get("og:description", "") or kw["brand"]["tagline"][kw["lang"]]
    existing_ld = LDJSON_RE.findall(head)
    dates = kw.get("dates")
    if dates:
        head = LDJSON_RE.sub(lambda m: '<script type="application/ld+json">' + _fix_article_dates(m.group(1), *dates) + "</script>", head)
    for rx in STRIP_HEAD_RE:
        head = rx.sub("", head)
    kind = kw.get("kind") or page_kind(kw["dest"])
    og_type = kw.pop("og_type", None) or ogs.get("og:type") or ("article" if kind in ("article", "guide") else "website")
    new_title, new_desc, block = build_head(title=title, description=desc, existing_ld=existing_ld, og_type=og_type, **kw)
    head = TITLE_RE.sub(lambda m: f"<title>{esc(new_title)}</title>", head, count=1) if tm else head + f"<title>{esc(new_title)}</title>\n"
    # keep the head tidy: collapse runs of blank lines
    head = re.sub(r"\n{3,}", "\n\n", head)
    info = {"title": new_title, "description": new_desc, "og_image": kw["og_image"], "existing_og_image": ogs.get("og:image")}
    return head.rstrip() + "\n" + block + "\n" + body, info


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")
