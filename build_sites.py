#!/usr/bin/env python3
"""
build_sites.py — split site/ into one Cloudflare Pages dist per product domain.

    python build_sites.py            # builds dist/<domain>/ for every site
    python build_sites.py --only deskuptime.com

Edit SITES below to move files between domains. A file goes to the FIRST site
whose rules claim it; the site with "rest": True receives everything left over.
"""
from __future__ import annotations

import argparse
import fnmatch
import html as htmllib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from brand import BRANDS, BRAND_DIR  # noqa: E402
import pagepass  # noqa: E402
SITE = ROOT / "site"
DIST = ROOT / "dist"
AUDITEDWP_DIR = Path(os.environ.get("AUDITEDWP_DIR") or (ROOT.parent / "auditedwp"))
AUDITEDWP_DESKUPTIME = AUDITEDWP_DIR / "site" / "deskuptime"
OLD_ORIGIN = "https://hermes-passiv.pages.dev"

# ---------------------------------------------------------------------------
# MANIFEST — domain -> rules. Paths/globs are relative to site/.
#   include     : globs of files to copy (fnmatch on the relative posix path)
#   title_match : (glob, regex) — include files whose <title>/<h1> matches
#   remap       : {source-prefix: dest-prefix} — move directories in the dist
#   extra       : (absolute source file, source-key, dest-relative-path)
#                 source-key is the path the file "would have had" under site/
#                 so root-relative links to it can be resolved
#   index_from  : file (dest-relative) to duplicate as index.html if missing
#   rest        : True for the catch-all site
# ---------------------------------------------------------------------------
SITES: dict[str, dict] = {
    "cleancopy.tools": {
        "project": "cleancopy-tools",
        "product": "cleancopy",
        "brand": "Clean Copy",
        "github": "https://github.com/mahope/clean-copy",
        "nav": {
            "en": [("Extensions", "/#install"), ("CLI", "/clean-copy-cli-ref"), ("Tool", "/clean-copy-tool"),
                   ("Guides", "/blog/"), ("GitHub", "https://github.com/mahope/clean-copy")],
            "da": [("Udvidelser", "/da/#install"), ("CLI", "/clean-copy-cli-ref"), ("Værktøj", "/clean-copy-tool"),
                   ("Guides", "/blog/"), ("GitHub", "https://github.com/mahope/clean-copy")],
        },
        "include": [
            "clean-copy*.html",
            "copy-clean-guide.html",
            "url-to-markdown.html",
            "mcp.html",
            "clean-copy/**",
            "extension-zips/**",
            "clean-copy-core.js",
            "clean-copy-bookmarklet.js",
            "api-readme.md",
            "openapi.yaml",
            "da/url-til-markdown.html",
            "da/clean-copy.html",
            "downloads/clean-copy*",
        ],
        "title_match": [
            ("blog/*.html", r"Clean Copy|Markdown|clean-copy"),
            ("da/blog/*.html", r"Clean Copy|Markdown|clean-copy"),
        ],
        "index_from": {"index.html": "clean-copy.html", "da/index.html": "da/clean-copy.html"},
    },
    "deskuptime.com": {
        "project": "deskuptime",
        "product": "deskuptime",
        "brand": "DeskUptime",
        "github": "https://github.com/mahope/deskuptime",
        "nav": {
            "en": [("Tools", "/tools/"), ("Pro", "/#pro"), ("Docs", "https://github.com/mahope/deskuptime#readme"),
                   ("Compare", "/#compare")],
            "da": [("Værktøjer", "/tools/"), ("Pro", "/da/#pro"), ("Docs", "https://github.com/mahope/deskuptime#readme"),
                   ("Sammenlign", "/da/#compare")],
        },
        "include": ["deskuptime/**", "da/deskuptime/**"],
        "remap": {"deskuptime/": "", "da/deskuptime/": "da/"},
        "extra": [
            (AUDITEDWP_DESKUPTIME / "index.html", "deskuptime/tools/index.html", "tools/index.html"),
            (AUDITEDWP_DESKUPTIME / "bulk-url-checker" / "index.html",
             "deskuptime/bulk-url-checker/index.html", "bulk-url-checker/index.html"),
            (AUDITEDWP_DESKUPTIME / "security-headers-checker" / "index.html",
             "deskuptime/security-headers-checker/index.html", "security-headers-checker/index.html"),
        ],
    },
    "bugbottle.dev": {
        "project": "bugbottle-dev",
        "product": "bugbottle",
        "brand": "BugBottle",
        "github": "https://github.com/mahope/bugbottle",
        "nav": {
            "en": [("Demo", "/bugbottle-demo"), ("Docs", "https://github.com/mahope/bugbottle#readme"),
                   ("npm", "https://www.npmjs.com/package/bugbottle"), ("GitHub", "https://github.com/mahope/bugbottle")],
            "da": [("Demo", "/bugbottle-demo"), ("Docs", "https://github.com/mahope/bugbottle#readme"),
                   ("npm", "https://www.npmjs.com/package/bugbottle"), ("GitHub", "https://github.com/mahope/bugbottle")],
        },
        "include": [
            "bugbottle-demo.html",
            "bugbottle-demo.js",
            "hti-shim.js",
            "worker-bugbottle-demo.js",
            "blog/add-bug-report-form-to-any-website.html",
            "blog/bug-reports-in-ci-pipeline.html",
            "da/blog/bugrapporter-i-ci-pipeline.html",
            "da/blog/tilfoej-fejlrapport-formular-hjemmeside.html",
        ],
        "extra": [
            (ROOT / "bugbottle-landing" / "index.html", "bugbottle-landing/index.html", "index.html"),
            (ROOT / "bugbottle-landing" / "da" / "index.html", "bugbottle-landing/da/index.html", "da/index.html"),
        ],
    },
    "mahope.tools": {
        "project": "mahope-tools",
        "product": "mahope",
        "brand": "mahope.tools",
        "github": "https://github.com/mahope",
        "nav": {
            "en": [("Tools", "/free-tools"), ("Books", "/books/"), ("Blog", "/blog/"),
                   ("Clean Copy", "https://cleancopy.tools"), ("Compliance", "/compliance-guide")],
            "da": [("Værktøjer", "/free-tools"), ("Bøger", "/books/"), ("Blog", "/blog/"),
                   ("Clean Copy", "https://cleancopy.tools/da/"), ("Compliance", "/da/compliance-site-check")],
        },
        "rest": True,
        "index_from": "free-tools.html",
    },
}

# Copied into every dist (never "claimed" by a single site).
SHARED = ["style.css", "track.js", "shell.js", "_worker.js"]
# Never copied (regenerated per site, or junk).
SKIP_NAMES = {"sitemap.xml", "robots.txt"}
SKIP_SUFFIXES = (".orig", ".bak")
SKIP_DIRS = ("_partials/", "_brand/")
# Root-relative refs to these extensions are auto-pulled into a dist if the
# file exists in site/ (og:image, icons, extra css/js…).
ASSET_EXT = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".css", ".js", ".woff", ".woff2"}
TEXT_EXT = {".html", ".htm", ".xml", ".js", ".json", ".txt", ".md", ".yaml", ".yml", ".css", ".webmanifest"}
# Worker routes exist on every site; never count them as broken.
WORKER_PREFIXES = ("/api/", "/scan-proxy")
# Files generated per dist by write_site (root-relative). Never "broken".
GENERATED = ("/sitemap.xml", "/robots.txt", "/wrangler.toml", "/llms.txt", "/llms-full.txt", "/humans.txt",
             "/.well-known/security.txt", "/404.html", "/favicon.svg", "/favicon.ico", "/apple-touch-icon.png",
             "/icon-192.png", "/icon-512.png", "/site.webmanifest", "/og.png", "/og-da.png",
             "/search-index.json", "/search/", "/da/search/", "/search/index.html", "/da/search/index.html")


# ---------------------------------------------------------------------------
def rel(p: Path, base: Path = SITE) -> str:
    return p.relative_to(base).as_posix()


def matches(relpath: str, glob: str) -> bool:
    if glob.endswith("/**"):
        return relpath.startswith(glob[:-3] + "/")
    return fnmatch.fnmatchcase(relpath, glob)


def title_of(path: Path) -> str:
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:20000]
    except OSError:
        return ""
    t = re.search(r"<title>(.*?)</title>", head, re.S | re.I)
    h = re.search(r"<h1[^>]*>(.*?)</h1>", head, re.S | re.I)
    return (t.group(1) if t else "") + " | " + (re.sub(r"<[^>]+>", "", h.group(1)) if h else "")


def url_variants(relpath: str) -> list[str]:
    """All URL paths that would hit this file on Pages."""
    p = "/" + relpath
    out = [p]
    if p.endswith("/index.html"):
        d = p[: -len("index.html")]
        out += [d, d.rstrip("/") or "/"]
    elif p.endswith(".html"):
        out += [p[:-5], p[:-5] + "/"]
    return out


def canonical_url(relpath: str) -> str:
    p = "/" + relpath
    if p.endswith("/index.html"):
        return p[: -len("index.html")]
    if p.endswith(".html"):
        return p[:-5]
    return p


def apply_remap(relpath: str, remap: dict[str, str]) -> str:
    for src, dst in remap.items():
        if relpath.startswith(src):
            return dst + relpath[len(src):]
    return relpath


# ---------------------------------------------------------------------------
class Site:
    def __init__(self, domain: str, cfg: dict):
        self.domain = domain
        self.cfg = cfg
        self.project = cfg["project"]
        self.remap = cfg.get("remap", {})
        # source-key (site-relative) -> (absolute source path, dest-relative path)
        self.files: dict[str, tuple[Path, str]] = {}
        self.rewritten = 0
        self.shelled = 0
        self.cross = 0
        self.broken: dict[str, int] = {}

    @property
    def dist(self) -> Path:
        return DIST / self.domain

    def add(self, src_key: str, src: Path, dest: str | None = None):
        self.files[src_key] = (src, dest or apply_remap(src_key, self.remap))


def select_files(sites: dict[str, Site]) -> None:
    all_files = sorted(p for p in SITE.rglob("*") if p.is_file())
    claimed: set[str] = set()
    for domain, site in sites.items():
        cfg = site.cfg
        if cfg.get("rest"):
            continue
        for p in all_files:
            r = rel(p)
            if r in claimed or p.name in SKIP_NAMES or r.endswith(SKIP_SUFFIXES) or r in SHARED or r.startswith(SKIP_DIRS):
                continue
            hit = any(matches(r, g) for g in cfg.get("include", []))
            if not hit:
                for glob, rx in cfg.get("title_match", []):
                    if matches(r, glob) and re.search(rx, title_of(p), re.I):
                        hit = True
                        break
            if hit:
                site.add(r, p)
                claimed.add(r)
        for src, key, dest in cfg.get("extra", []):
            if not src.exists():
                print(f"  WARN {domain}: extra file missing: {src}")
                continue
            site.add(key, src, dest)
    for site in sites.values():
        if site.cfg.get("rest"):
            for p in all_files:
                r = rel(p)
                if r in claimed or p.name in SKIP_NAMES or r.endswith(SKIP_SUFFIXES) or r in SHARED or r.startswith(SKIP_DIRS):
                    continue
                site.add(r, p)
    for site in sites.values():
        for name in SHARED:
            p = SITE / name
            if p.exists():
                site.add(name, p)


ASSET_REF = re.compile(r"""(?:href|src|content|poster)=["'](/[^"'?#\s]+)|url\((/[^)"'?#\s]+)\)""")


def pull_assets(site: Site) -> int:
    """Add site/ assets referenced root-relatively by this site's files."""
    added = 0
    for _ in range(3):  # css may reference images etc.
        new: dict[str, Path] = {}
        for key, (src, _dest) in site.files.items():
            if src.suffix.lower() not in TEXT_EXT:
                continue
            text = src.read_text(encoding="utf-8", errors="ignore")
            for m in ASSET_REF.finditer(text):
                path = m.group(1) or m.group(2)
                if Path(path).suffix.lower() not in ASSET_EXT:
                    continue
                r = path.lstrip("/")
                if r in site.files or r in new:
                    continue
                cand = SITE / r
                if cand.is_file():
                    new[r] = cand
        if not new:
            break
        for r, p in new.items():
            site.add(r, p, r)  # assets keep their path (no remap)
            added += 1
    return added


def build_index(sites: dict[str, Site]):
    """source URL variant -> (domain, dest canonical url)"""
    global_idx: dict[str, tuple[str, str]] = {}
    local_idx: dict[str, dict[str, str]] = {}
    for domain, site in sites.items():
        local: dict[str, str] = {}
        for key, (_src, dest) in site.files.items():
            target = canonical_url(dest)
            for v in url_variants(key):
                local.setdefault(v, target)
                global_idx.setdefault(v, (domain, target))
            # dest variants too, so already-remapped links keep working
            for v in url_variants(dest):
                local.setdefault(v, target)
        # generated per site, so they always exist locally
        for gen in GENERATED:
            local[gen] = gen
        local_idx[domain] = local
    return global_idx, local_idx


# ---------------------------------------------------------------------------
# scheme-less display text ("hermes-passiv.pages.dev/foo") is rewritten too;
# the lookbehind leaves escaped regex literals in _worker.js alone.
ABS_RE = re.compile(r"(?<![\.\w])(https?://)?" + re.escape(OLD_ORIGIN.split("//")[1]) + r"(/[^\s\"'<>)\]]*)?")
ATTR_RE = re.compile(r"""((?:href|src|content|action|poster|data-href)=["'])(/[^"'\s]*)(["'])""")
CSSURL_RE = re.compile(r"""(url\(["']?)(/[^)"'\s]+)(["']?\))""")


def rewrite_text(site: Site, text: str, is_html: bool, local: dict, global_idx: dict) -> str:
    own = "https://" + site.domain

    def resolve(path: str) -> tuple[str | None, str]:
        """returns (new absolute-or-local path or None if unchanged, kind)"""
        m = re.match(r"([^?#]*)(.*)", path)
        base, suffix = m.group(1), m.group(2)
        if base == "" or base == "/":
            return None, "root"
        if base in local:
            new = local[base] + suffix
            return (new if new != path else None), "local"
        if base in global_idx:
            domain, target = global_idx[base]
            return "https://" + domain + target + suffix, "cross"
        if base.startswith(WORKER_PREFIXES):
            return None, "worker"
        remapped = "/" + apply_remap(base.lstrip("/"), site.remap)
        return (remapped + suffix if remapped != base else None), "broken"

    def abs_sub(m: re.Match) -> str:
        scheme, path = m.group(1) or "", m.group(2) or "/"
        new, kind = resolve(path)
        if kind == "cross":
            site.cross += 1
            return new if scheme else new.split("//", 1)[1]
        if kind == "broken":
            site.broken[path] = site.broken.get(path, 0) + 1
        site.rewritten += 1
        return (own if scheme else site.domain) + (new if new else path)

    text = ABS_RE.sub(abs_sub, text)
    if not is_html:
        return text

    def attr_sub(m: re.Match) -> str:
        new, kind = resolve(m.group(2))
        if kind == "cross":
            site.cross += 1
            return m.group(1) + new + m.group(3)
        if kind == "broken":
            site.broken[m.group(2)] = site.broken.get(m.group(2), 0) + 1
        if new:
            site.rewritten += 1
            return m.group(1) + new + m.group(3)
        return m.group(0)

    text = ATTR_RE.sub(attr_sub, text)

    def css_sub(m: re.Match) -> str:
        new, kind = resolve(m.group(2))
        if kind == "cross":
            site.cross += 1
            return m.group(1) + new + m.group(3)
        if new:
            site.rewritten += 1
            return m.group(1) + new + m.group(3)
        return m.group(0)

    return CSSURL_RE.sub(css_sub, text)



# ---------------------------------------------------------------------------
# Shared shell: family bar + header + footer partials injected into every HTML page,
# breadcrumbs, article layout (prose + TOC), BugBottle tag, search index.
# ---------------------------------------------------------------------------
PARTIALS = SITE / "_partials"
# The family, in the order it appears in the bar and the footer on every site.
FAMILY = [
    ("EUComply", "EU Comply Pro", "https://eucomplypro.com"),
    ("Clean Copy", "Clean Copy", "https://cleancopy.tools"),
    ("DeskUptime", "DeskUptime", "https://deskuptime.com"),
    ("Transmute", "Transmute", "https://transmute.run"),
    ("BugBottle", "BugBottle", "https://bugbottle.dev"),
    ("All tools", "mahope.tools", "https://mahope.tools"),
]
PRODUCTS = [(full, url) for _short, full, url in FAMILY]
BUGBOTTLE_VERSION = "0.5.0"
BUGBOTTLE_ENDPOINT = "https://mahope.tools/api/bugreport"
L10N = {
    "en": dict(skip_label="Skip to content", nav_label="Main", menu_label="Menu", brand_by="by mahoje.dk",
               family_label="Mahope tools:", family_heading="Family", site_heading="Site",
               privacy_link="Privacy", security_link="Security", sitemap_link="Sitemap", report_link="Report a bug",
               report_subject="Bug%20report", bb_badge="Feedback powered by BugBottle",
               privacy_note="No cookies, no trackers — only an anonymous page-view counter we run ourselves.",
               maker_note='Built by Mads Holst Jensen · <a href="https://mahoje.dk">mahoje.dk</a> — developer and technical partner for small businesses, Odense, Denmark.',
               license_note='<span>MIT-licensed — source on <a href="{github}">GitHub</a></span>',
               search_label="Search", search_placeholder="Search pages, tools and guides…", search_hint="Type to search every page on this site.",
               search_nav="navigate", search_open="open", search_close="close", theme_label="Theme: system",
               search_title="Search {brand}", search_heading="Search this site", search_description="Search every page, tool and guide on this site.",
               noscript="Search needs JavaScript. Try the sitemap instead.",
               home="Home", blog="Blog", guides="Guides", books="E-books", tools="Tools", pages="Pages",
               updated="Updated", read="min read", on_this_page="On this page", share="Copy link", newer="Newer", older="Older"),
    "da": dict(skip_label="Spring til indhold", nav_label="Hovedmenu", menu_label="Menu", brand_by="af mahoje.dk",
               family_label="Mahope tools:", family_heading="Familien", site_heading="Sitet",
               privacy_link="Privatliv", security_link="Sikkerhed", sitemap_link="Sitemap", report_link="Rapportér en fejl",
               report_subject="Fejlrapport", bb_badge="Feedback drevet af BugBottle",
               privacy_note="Ingen cookies, ingen trackere — kun en anonym sidevisningstæller, vi selv kører.",
               maker_note='Lavet af Mads Holst Jensen · <a href="https://mahoje.dk">mahoje.dk</a> — udvikler og teknisk partner for små virksomheder, Odense.',
               license_note='<span>MIT-licens — kildekode på <a href="{github}">GitHub</a></span>',
               search_label="Søg", search_placeholder="Søg i sider, værktøjer og guides…", search_hint="Skriv for at søge på hele sitet.",
               search_nav="navigér", search_open="åbn", search_close="luk", theme_label="Tema: system",
               search_title="Søg på {brand}", search_heading="Søg på sitet", search_description="Søg i alle sider, værktøjer og guides på sitet.",
               noscript="Søgning kræver JavaScript. Prøv sitemappet i stedet.",
               home="Forside", blog="Blog", guides="Guides", books="E-bøger", tools="Værktøjer", pages="Sider",
               updated="Opdateret", read="min. læsning", on_this_page="På denne side", share="Kopiér link", newer="Nyere", older="Ældre"),
}
BODY_RE = re.compile(r"<body[^>]*>", re.I)
BODY_END_RE = re.compile(r"</body>", re.I)
HEAD_END_RE = re.compile(r"</head>", re.I)
HTML_TAG_RE = re.compile(r"<html([^>]*)>", re.I)
FIRST_HEADER_RE = re.compile(r"\s*<header\b[^>]*>.*?</header>", re.S | re.I)
FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.S | re.I)
FOOTER_NAV_RE = re.compile(r'\s*<nav aria-label="Footer">.*?</nav>', re.S | re.I)
HREFLANG_RE = re.compile(r'<link[^>]+hreflang="(en|da)"[^>]+href="([^"]+)"|<link[^>]+href="([^"]+)"[^>]+hreflang="(en|da)"', re.I)
MAIN_OPEN_RE = re.compile(r"<main\b[^>]*>", re.I)
HERO_RE = re.compile(r"<(header|div)\s+class=\"(?:hero|book-header)[^\"]*\"[^>]*>.*?</\1>", re.S | re.I)
HEADING_RE = re.compile(r"<(h2|h3)\b([^>]*)>(.*?)</\1>", re.S | re.I)
IMG_RE = re.compile(r"<img(\s[^>]*)>", re.I)
EXT_A_RE = re.compile(r'<a\b([^>]*\shref="https?://[^"]+"[^>]*)>', re.I)
TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style|noscript|svg|template)\b.*?</\1>", re.S | re.I)
# split() variant: parts[0::3] is prose, parts[1::3] the skipped blocks (verbatim), parts[2::3] the tag names
SKIP_SPLIT_RE = re.compile(r"(<(script|style|noscript|svg|template|pre|textarea|code)\b.*?</\2>)", re.S | re.I)
LEGACY_CRUMBS_RE = re.compile(r"\s*<(p|nav|div)\s+class=\"breadcrumb\"[^>]*>.*?</\1>", re.S | re.I)
TOOL_MAIN_RE = re.compile(r'<main\b([^>]*\sclass="[^"]*\b(?:[\w-]+-)?wrap\b[^"]*"[^>]*)>', re.I)


def _main_end(text: str) -> int:
    """Offset of the last </main> that is not inside script/style/pre/textarea/code (generator pages
    carry whole HTML documents in templates). -1 when there is none."""
    spans = [m.span() for m in SKIP_SPLIT_RE.finditer(text)]
    for m in reversed(list(re.finditer(r"</main>", text, re.I))):
        if not any(a <= m.start() < b for a, b in spans):
            return m.start()
    return -1


def _join_skip(parts: list[str]) -> str:
    """Re-join a SKIP_SPLIT_RE.split() result: drop the tag-name captures at parts[2::3]."""
    return "".join(p for i, p in enumerate(parts) if i % 3 != 2)


def _partial(name: str) -> str:
    return (PARTIALS / name).read_text(encoding="utf-8")


def _render(tpl: str, ctx: dict) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(ctx.get(m.group(1), "")), tpl)


def _nav_links(links, current: str, indent: str = "      ") -> str:
    out = []
    for label, href in links:
        cur = ' aria-current="page"' if href == current else ""
        ext = ' class="ext" rel="noopener"' if href.startswith("http") else ""
        out.append(f'{indent}<a href="{href}"{cur}{ext}>{label}</a>')
    return "\n".join(out)


def _alternates(head: str) -> dict:
    alts = {}
    for m in HREFLANG_RE.finditer(head):
        lang, href = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
        alts.setdefault(lang.lower(), href)
    return alts


def _lang_switch(lang: str, alts: dict[str, str]) -> str:
    if "en" in alts and "da" in alts and alts["en"] != alts["da"]:
        parts = []
        for code in ("en", "da"):
            if code == lang:
                parts.append(f'<span aria-current="true" lang="{code}">{code.upper()}</span>')
            else:
                parts.append(f'<a href="{alts[code]}" lang="{code}" hreflang="{code}">{code.upper()}</a>')
        return '      <span class="lang-switch">' + "".join(parts) + "</span>"
    # keep the space so the header never shifts between translated and untranslated pages
    return '      <span class="lang-switch is-empty" aria-hidden="true"><span>EN</span><span>DA</span></span>'


def slugify(text: str) -> str:
    t = htmllib.unescape(TAG_RE.sub("", text)).lower()
    t = re.sub(r"[^a-z0-9æøå]+", "-", t).strip("-")
    return t[:60] or "section"


def text_of(html: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(TAG_RE.sub(" ", SCRIPT_STYLE_RE.sub(" ", html)))).strip()


def section_of(dest: str, text: str, lang: str) -> str:
    t = L10N[lang]
    d = dest[3:] if dest.startswith("da/") else dest
    if d.startswith("blog/"):
        return t["blog"]
    if d.startswith("guides/"):
        return t["guides"]
    if d.startswith("books/"):
        return t["books"]
    if d in ("index.html",):
        return t["pages"]
    if re.search(r"<(form|textarea|input)\b", text, re.I) and "/" not in d:
        return t["tools"]
    return t["pages"]


def crumbs_for(site: Site, dest: str, lang: str, title: str, section: str) -> list[tuple[str, str]]:
    """[(label, url)] — home, optional section index, current page."""
    t = L10N[lang]
    home = "/da/" if lang == "da" else "/"
    if dest in ("index.html", "da/index.html"):
        return []
    out = [(t["home"], home)]
    d = dest[3:] if dest.startswith("da/") else dest
    prefix = "da/" if dest.startswith("da/") else ""
    dests = {v[1] for v in site.files.values()}
    for folder, key in (("blog/", "blog"), ("guides/", "guides"), ("books/", "books")):
        if d.startswith(folder) and d != folder + "index.html":
            if prefix + folder + "index.html" in dests:
                out.append((t[key], "/" + prefix + folder))
            elif folder + "index.html" in dests:
                out.append((t[key], "/" + folder))
            break
    else:
        if section == t["tools"] and site.cfg["product"] == "mahope":
            out.append((t["tools"], "/free-tools"))
    out.append((title, canonical_url(dest)))
    return out


def _crumbs_html(crumbs: list[tuple[str, str]], lang: str) -> str:
    if not crumbs:
        return ""
    items = []
    for i, (label, url) in enumerate(crumbs):
        if i == len(crumbs) - 1:
            items.append(f'<li aria-current="page">{esc_html(label)}</li>')
        else:
            items.append(f'<li><a href="{url}">{esc_html(label)}</a></li>')
    label = "Brødkrumme" if lang == "da" else "Breadcrumb"
    return f'<nav class="crumbs container" aria-label="{label}"><ol>' + "".join(items) + "</ol></nav>\n"


def esc_html(s: str) -> str:
    return htmllib.escape(htmllib.unescape(s), quote=True)


def _reading_minutes(html: str) -> int:
    words = len(text_of(html).split())
    return max(1, round(words / 220))


def _toc(article: str) -> tuple[str, list[tuple[str, str, str]]]:
    """Give every h2/h3 an id; return (article, [(level, id, text)])."""
    used: set[str] = set()
    entries: list[tuple[str, str, str]] = []

    def sub(m: re.Match) -> str:
        level, attrs, inner = m.group(1).lower(), m.group(2), m.group(3)
        idm = re.search(r'\sid="([^"]*)"', attrs)
        text = re.sub(r"\s+", " ", htmllib.unescape(TAG_RE.sub("", inner))).strip()
        if not text or len(text) > 120:
            return m.group(0)
        if idm:
            hid = idm.group(1)
        else:
            base = slugify(text)
            hid, n = base, 2
            while hid in used:
                hid, n = f"{base}-{n}", n + 1
            attrs = attrs + f' id="{hid}"'
        used.add(hid)
        entries.append((level, hid, text))
        return f"<{level}{attrs}>{inner}</{level}>"

    parts = SKIP_SPLIT_RE.split(article)
    for i in range(0, len(parts), 3):
        parts[i] = HEADING_RE.sub(sub, parts[i])
    return _join_skip(parts), entries


def _toc_html(entries, lang: str) -> str:
    entries = [e for e in entries if e[0] == "h2" or len(entries) < 25]
    if len([e for e in entries if e[0] == "h2"]) < 2:
        return ""
    items = "".join(f'<li class="lvl{lvl[1]}"><a href="#{htmllib.escape(hid, quote=True)}">{esc_html(text)}</a></li>' for lvl, hid, text in entries)
    return f'<nav class="toc" aria-label="{L10N[lang]["on_this_page"]}"><details><summary>{L10N[lang]["on_this_page"]}</summary><ol>{items}</ol></details></nav>'


def article_layout(text: str, lang: str, dates, neighbours: dict) -> str:
    """Blog/guide: wrap everything after the hero in .prose-layout with a sidebar (meta, TOC, prev/next)."""
    mm = MAIN_OPEN_RE.search(text)
    if not mm:
        return text
    end = _main_end(text)
    if end < 0:
        return text
    body_start = mm.end()
    inner = text[body_start:end]
    hm = HERO_RE.search(inner)
    if hm:
        hero, rest = inner[: hm.end()], inner[hm.end():]
    else:
        hero, rest = "", inner
    if not rest.strip():
        return text
    rest, entries = _toc(rest)
    t = L10N[lang]
    meta = []
    if dates:
        meta.append(f'<span>{t["updated"]} <time datetime="{dates[1]}">{dates[1]}</time></span>')
    meta.append(f'<span>{_reading_minutes(rest)} {t["read"]}</span>')
    meta.append(f'<button type="button" class="share-btn" data-copy-link><svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/></svg>{t["share"]}</button>')
    aside = '<aside class="prose-aside"><div class="article-meta">' + "".join(meta) + "</div>" + _toc_html(entries, lang) + "</aside>"
    pn = ""
    prev_p, next_p = neighbours.get("prev"), neighbours.get("next")
    if prev_p or next_p:
        pn = '<nav class="prev-next" aria-label="Previous and next">'
        pn += f'<a class="prev" href="{prev_p[0]}"><span class="lbl">← {t["newer"]}</span>{esc_html(prev_p[1])}</a>' if prev_p else "<span></span>"
        pn += f'<a class="next" href="{next_p[0]}"><span class="lbl">{t["older"]} →</span>{esc_html(next_p[1])}</a>' if next_p else "<span></span>"
        pn += "</nav>"
    new_inner = hero + '\n<div class="container prose-layout">\n<article class="prose">' + rest + pn + "</article>\n" + aside + "\n</div>\n"
    return text[:body_start] + new_inner + text[end:]


def lazy_images(text: str) -> str:
    def sub(m: re.Match) -> str:
        a = m.group(1)
        if "loading=" in a:
            return m.group(0)
        return f'<img{a} loading="lazy" decoding="async">'
    parts = SKIP_SPLIT_RE.split(text)
    for i in range(0, len(parts), 3):
        parts[i] = IMG_RE.sub(sub, parts[i])
    return _join_skip(parts)


def mark_external(text: str, domain: str) -> str:
    def sub(m: re.Match) -> str:
        a = m.group(1)
        host = re.search(r'href="https?://([^/"]+)', a).group(1)
        if host.endswith(domain) or host.endswith("mahoje.dk"):
            return m.group(0)
        if 'rel="' in a:
            a = re.sub(r'rel="([^"]*)"', lambda r: f'rel="{r.group(1)}"' if "noopener" in r.group(1) else f'rel="{r.group(1)} noopener"', a)
        else:
            a += ' rel="noopener"'
        if 'class="' in a:
            a = re.sub(r'class="([^"]*)"', lambda c: c.group(0) if "ext" in c.group(1).split() else f'class="{c.group(1)} ext"', a, count=1)
        else:
            a += ' class="ext"'
        return f"<a{a}>"
    parts = SKIP_SPLIT_RE.split(text)
    for i in range(0, len(parts), 3):
        parts[i] = EXT_A_RE.sub(sub, parts[i])
    return _join_skip(parts)


def git_dates() -> dict[str, tuple[str, str]]:
    """source path (repo-relative posix) -> (first commit date, last commit date), ISO dates."""
    try:
        out = subprocess.run(["git", "log", "--format=%x01%cI", "--name-only", "--", "site", "bugbottle-landing"],
                             cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="ignore", check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}
    dates: dict[str, tuple[str, str]] = {}
    cur = ""
    for line in out.splitlines():
        if line.startswith("\x01"):
            cur = line[1:11]
        elif line.strip():
            f = line.strip()
            first, last = dates.get(f, (cur, cur))
            dates[f] = (cur, last)  # log is newest-first: keep first-seen as last, overwrite first
    return dates


def hreflang_pairs(sites: dict[str, Site], global_idx: dict, local_idx: dict) -> dict[str, dict[str, str]]:
    """absolute page url -> {"en": url, "da": url}, symmetric, built from the pages' own hreflang links."""
    pairs: dict[str, dict[str, str]] = {}
    # sources of index copies canonicalise to the index url
    alias: dict[str, str] = {}
    for s in sites.values():
        idx_cfg = s.cfg.get("index_from")
        idx_map = {"index.html": idx_cfg} if isinstance(idx_cfg, str) else (idx_cfg or {})
        for tgt, srcf in idx_map.items():
            if srcf:
                alias[f"https://{s.domain}{canonical_url(srcf)}"] = f"https://{s.domain}{canonical_url(tgt)}"

    def resolve(href: str) -> str | None:
        host = re.match(r"^https?://([^/]+)", href)
        path = re.sub(r"^https?://[^/]+", "", href) or "/"
        path = path.split("#")[0].split("?")[0]
        if host and host.group(1) in sites:  # already on one of our domains: look there only
            local = local_idx[host.group(1)]
            if path in ("/", "/da/"):
                return f"https://{host.group(1)}{path}"
            if path in local:
                u = f"https://{host.group(1)}{local[path]}"
                return alias.get(u, u)
            return None
        if path in global_idx:
            domain, target = global_idx[path]
            u = f"https://{domain}{target}"
            return alias.get(u, u)
        return None

    for site in sites.values():
        for key, (src, dest) in site.files.items():
            if src.suffix.lower() not in (".html", ".htm"):
                continue
            text = src.read_text(encoding="utf-8", errors="ignore")
            head_end = HEAD_END_RE.search(text)
            head = text[: head_end.start()] if head_end else text[:6000]
            lang = "da" if re.search(r'<html[^>]*lang="da"', text[:400], re.I) else "en"
            own = f"https://{site.domain}{canonical_url(dest)}"
            own = alias.get(own, own)
            other = "da" if lang == "en" else "en"
            alt = _alternates(head).get(other)
            target = resolve(alt) if alt else None
            if not target or target == own:
                continue
            for u in (own, target):
                pairs.setdefault(u, {})
                pairs[u][lang] = own
                pairs[u][other] = target
    return pairs


def bugbottle_tag(site: Site, lang: str) -> str:
    brand = BRANDS[site.cfg["product"]]
    return (f'<script src="https://cdn.jsdelivr.net/npm/bugbottle@{BUGBOTTLE_VERSION}/dist/bugbottle.js" defer '
            f'data-endpoint="{BUGBOTTLE_ENDPOINT}" data-locale="{lang}" data-primary="{brand["accent"]}" '
            f'data-brand="{site.cfg["brand"]}" data-position="bottom-right" data-scrub></script>')


def apply_shell(site: Site, key: str, dest: str, text: str, alts: dict[str, str], *, title: str = "",
                dates=None, neighbours: dict | None = None, kind: str | None = None) -> tuple[str, dict]:
    """Inject family bar, header, breadcrumbs, article layout, footer, scripts. Returns (html, info)."""
    cfg = site.cfg
    info: dict = {"crumbs": [], "section": "", "toc": False}
    if "brand" not in cfg or not BODY_RE.search(text):
        return text, info
    lang = "da" if re.search(r'<html[^>]*lang="da"', text[:400], re.I) else "en"
    t = L10N[lang]
    brand = BRANDS[cfg["product"]]
    home = "/da/" if lang == "da" else "/"
    search_url = "/da/search/" if lang == "da" else "/search/"
    current = canonical_url(dest)
    sw = _lang_switch(lang, alts)
    own_url = "https://" + site.domain
    fam = []
    for short, _full, url in FAMILY:
        cur = ' aria-current="true"' if url == own_url else ""
        cls = ' class="family-all"' if short == "All tools" else ""
        href = url if url == own_url else url + ("/da/" if lang == "da" and url.split("//")[1] in SITES else "")
        fam.append(f'<a href="{href}"{cur}{cls}>{short}</a>')
    footer_links = [(label, href) for label, href in cfg["nav"][lang] if not href.startswith("http")]
    footer_links += [("GitHub", cfg["github"]), ("Releases" if lang == "en" else "Udgivelser", cfg["github"] + "/releases")] if cfg["product"] != "mahope" else []
    ctx = dict(t, brand=cfg["brand"], home=home, nav=_nav_links(cfg["nav"][lang], current), lang_switch=sw,
               family_links="\n".join(fam), search_url=search_url,
               product_line=brand["tagline"][lang],
               footer_links=_nav_links(footer_links, current, "          ").replace("<a ", "<li><a ").replace("</a>", "</a></li>"),
               product_links="\n".join('          <li><a href="%s"%s>%s</a></li>' % (u, ' aria-current="true"' if u == own_url else "", n) for n, u in PRODUCTS),
               privacy_url="/privacy/" if (SITE / "privacy" / "index.html").exists() and cfg["product"] == "mahope" else "https://mahope.tools/privacy/",
               maker_note=t["maker_note"], year=datetime.now(timezone.utc).year,
               license_note=t["license_note"].format(github=cfg["github"]) if cfg["product"] != "mahope" else "")
    header = _render(_partial("header.html"), ctx)
    footer = _render(_partial("footer.html"), ctx)

    def html_sub(m):
        attrs = m.group(1)
        if "data-product" in attrs:
            return m.group(0)
        return f'<html{attrs} data-product="{cfg["product"]}">'
    text = HTML_TAG_RE.sub(html_sub, text, count=1)

    # body: drop an old chrome header (a <header> without <h1> right after <body>), inject ours
    bm = BODY_RE.search(text)
    body_start = bm.end()
    m = FIRST_HEADER_RE.match(text, body_start)
    if m and not re.search(r"<h1\b", m.group(0), re.I):
        text = text[: m.start()] + text[m.end():]
    text = FOOTER_NAV_RE.sub("", text)
    # footer: replace the last <footer>…</footer>, else insert before </body>
    footers = list(FOOTER_RE.finditer(text))
    if footers:
        f = footers[-1]
        text = text[: f.start()] + footer + text[f.end():]
    else:
        text = re.sub(r"</body>", footer + "\n</body>", text, count=1, flags=re.I)
    # main: exactly one <main id="main"> around the page content
    if re.search(r"<main\b", text, re.I):
        mo = re.search(r"<main\b([^>]*)>", text, re.I)
        attrs = mo.group(1)
        # main is always full-width: no inline style, no .container on the element itself
        attrs = re.sub(r'\s+style="[^"]*"', "", attrs)
        had_container = bool(re.search(r'class="[^"]*\bcontainer\b', attrs))
        attrs = re.sub(r'class="([^"]*)"', lambda c: 'class="%s"' % " ".join(x for x in c.group(1).split() if x != "container"), attrs)
        attrs = attrs.replace(' class=""', "")
        if 'id="main"' not in attrs:
            attrs = ' id="main"' + attrs
        open_tag = f"<main{attrs}>" + ('\n<div class="container">' if had_container else "")
        end = _main_end(text)
        if end < 0:
            # unclosed <main>: close it right before the page's own footer (or </body>)
            fm = re.search(r"<footer\b|</body>", text[mo.end():], re.I)
            at = mo.end() + fm.start()
            text = text[:at] + "</main>\n" + text[at:]
            end = at
        close_tag = ("</div>\n" if had_container else "") + "</main>"
        # anything the page put between <body> and <main> (its own skip link, family bar, chrome
        # header, a hero with the h1, CTA strips) is dropped when it is chrome and moved inside main
        # when it is content — so main always starts right under the shared header
        pre = text[body_start: mo.start()]
        pre = re.sub(r'<a\s+class="skip[^"]*"[^>]*>.*?</a>', "", pre, flags=re.S | re.I)
        pre = re.sub(r"<nav\b[^>]*>.*?</nav>", "", pre, flags=re.S | re.I)
        pre = re.sub(r"<header\b[^>]*>.*?</header>", lambda h: h.group(0) if re.search(r"<h1\b", h.group(0), re.I) else "", pre, flags=re.S | re.I)
        text = (text[:body_start] + "\n" + header + "\n" + open_tag + pre + text[mo.end():end] + close_tag + text[end + len("</main>"):])
    else:
        fpos = text.rfind('<footer class="site-footer">')
        inner = text[body_start:fpos]
        if 'class="container' not in inner and not re.search(r'class="[^"]*wrap', inner):
            inner = '\n<div class="container">' + inner + "</div>\n"
        text = text[:body_start] + "\n" + header + '\n<main id="main">' + inner + "</main>\n" + text[fpos:]
    # tool pages: <main class="x-wrap"> becomes a wide container inside a full-width main
    tm = TOOL_MAIN_RE.search(text)
    if tm and "layout-wide" not in tm.group(1):
        end = _main_end(text)
        if end > tm.end():
            # "<main class="x-wrap">" is a tool page (wide); a plain "wrap" is ordinary content
            wide = bool(re.search(r'class="[^"]*\b[\w-]+-wrap\b', tm.group(1)))
            attrs = tm.group(1).replace('class="', 'class="layout-wide ') if wide else tm.group(1)
            text = (text[: tm.start()] + f'<main{attrs}>\n<div class="container{" tool" if wide else ""}">'
                    + text[tm.end():end] + "</div>\n" + text[end:])
    # breadcrumbs (visual) right after <main>
    mm = MAIN_OPEN_RE.search(text)
    main_html = text[mm.end(): _main_end(text)] if mm else ""
    section = section_of(dest, main_html, lang)
    info["section"] = section
    if kind is None:
        kind = pagepass.page_kind(dest)
    crumbs = crumbs_for(site, dest, lang, title or cfg["brand"], section) if kind != "home" else []
    info["crumbs"] = crumbs
    if crumbs and mm:
        # the shell's breadcrumbs replace any breadcrumb trail the page carried itself
        text = LEGACY_CRUMBS_RE.sub("", text, count=1)
        mm = MAIN_OPEN_RE.search(text)
        text = text[: mm.end()] + "\n" + _crumbs_html(crumbs, lang) + text[mm.end():]
    if kind in ("article", "guide"):
        text = article_layout(text, lang, dates, neighbours or {})
        info["toc"] = True
    text = lazy_images(text)
    text = mark_external(text, site.domain)
    # scripts: shell + BugBottle on every page (the demo page mounts its own copy)
    tags = f'<script src="/shell.js?v={pagepass.SHELL_VERSION}" defer></script>'
    if not dest.endswith("bugbottle-demo.html"):
        tags += "\n" + bugbottle_tag(site, lang)
    text = BODY_END_RE.sub(lambda m: tags + "\n</body>", text, count=1)
    site.shelled += 1
    return text, info


def og_image_for(site: Site, existing: str | None, lang: str, local: dict, global_idx: dict) -> str:
    own = "https://" + site.domain
    if existing:
        path = re.sub(r"^https?://[^/]+", "", existing)
        if path.startswith("/"):
            if path in local and not path.endswith(("/og.png", "/og-da.png")):
                return own + local[path]
            if path in global_idx:
                domain, target = global_idx[path]
                return f"https://{domain}{target}"
        elif existing.startswith("http"):
            return existing
    return own + ("/og-da.png" if lang == "da" else "/og.png")


def kv_namespace_id() -> str:
    toml = (SITE / "wrangler.toml").read_text(encoding="utf-8")
    m = re.search(r'binding\s*=\s*"VISITS"\s*\n\s*id\s*=\s*"([0-9a-f]+)"', toml)
    if not m:
        sys.exit("Could not find VISITS kv id in site/wrangler.toml")
    return m.group(1)


# ---------------------------------------------------------------------------
# Generated per-site files
# ---------------------------------------------------------------------------
HEADERS_TXT = """/*
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()
  Cross-Origin-Opener-Policy: same-origin
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https:; connect-src 'self' https://mahope.tools https:; frame-src 'self' https://www.youtube-nocookie.com; worker-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self' https:; frame-ancestors 'none'; upgrade-insecure-requests

/style.css
  Cache-Control: public, max-age=3600, stale-while-revalidate=86400

/*.png
  Cache-Control: public, max-age=604800

/*.svg
  Cache-Control: public, max-age=604800

/*.ico
  Cache-Control: public, max-age=604800

/*.jpg
  Cache-Control: public, max-age=604800
"""

NOT_FOUND = {
    "en": dict(title="Page not found", heading="That page is not here",
               body="The address may have changed, or the page was never on this site. Try one of these instead.",
               description="The page you asked for does not exist."),
    "da": dict(title="Siden findes ikke", heading="Den side er her ikke",
               body="Adressen kan være ændret, eller siden har aldrig ligget her. Prøv en af disse i stedet.",
               description="Den side, du bad om, findes ikke."),
}


def write_generated(site: Site, pages: list[dict]) -> None:
    """Sitemap, robots, llms, security.txt, humans.txt, _headers, 404, brand assets."""
    dist = site.dist
    own = "https://" + site.domain
    brand = BRANDS[site.cfg["product"]]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for f in (BRAND_DIR / site.cfg["product"]).iterdir():
        shutil.copy2(f, dist / f.name)

    urls = []
    for pg in sorted(pages, key=lambda p: p["url"]):
        alt = ""
        if pg["alternates"]:
            alt = "".join(f'<xhtml:link rel="alternate" hreflang="{c}" href="{u}"/>' for c, u in sorted(pg["alternates"].items()))
            alt += f'<xhtml:link rel="alternate" hreflang="x-default" href="{pg["alternates"].get("en", pg["url"])}"/>'
        urls.append(f'  <url><loc>{pg["url"]}</loc><lastmod>{pg["lastmod"]}</lastmod>{alt}</url>')
    (dist / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")

    (dist / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nDisallow: /api/\n\nSitemap: {own}/sitemap.xml\n\n"
        f"# Machine-readable summary for AI assistants: {own}/llms.txt\n", encoding="utf-8")

    install = "".join(f"- `{c}`\n" for c in brand.get("install", []))
    top = [p for p in pages if p["dest"].count("/") == 0 or p["dest"] == "da/index.html"]
    top = sorted(top, key=lambda p: (p["dest"] != "index.html", p["dest"]))[:40]
    llms = [f"# {brand['name']}", "", f"> {brand['summary']}", "",
            f"Site: {own}/ (English) and {own}/da/ (Danish). Made by Mads Holst Jensen, https://mahoje.dk. "
            f"Source: {brand['github']}. Contact: mads@mahoje.dk.", ""]
    if install:
        llms += ["## Install", "", install.rstrip(), ""]
    llms += ["## Pages", ""]
    llms += [f"- [{p['title']}]({p['url']}): {p['description']}" for p in top]
    llms += ["", f"Full page list: {own}/llms-full.txt", f"Sitemap: {own}/sitemap.xml", ""]
    (dist / "llms.txt").write_text("\n".join(llms), encoding="utf-8")
    full = [f"# {brand['name']} — all pages", "", brand["summary"], ""]
    for section in ("Pages", "Blog", "Guides", "Books", "Danish (da)"):
        sel = []
        for p in sorted(pages, key=lambda p: p["url"]):
            d = p["dest"]
            group = ("Danish (da)" if d.startswith("da/") else "Blog" if d.startswith("blog/") else
                     "Guides" if d.startswith("guides/") else "Books" if d.startswith("books/") else "Pages")
            if group == section:
                sel.append(f"- [{p['title']}]({p['url']}): {p['description']}")
        if sel:
            full += [f"## {section}", ""] + sel + [""]
    (dist / "llms-full.txt").write_text("\n".join(full), encoding="utf-8")

    wk = dist / ".well-known"
    wk.mkdir(exist_ok=True)
    expires = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
    (wk / "security.txt").write_text(
        f"Contact: mailto:mads@mahoje.dk\nExpires: {expires}\nPreferred-Languages: en, da\n"
        f"Canonical: {own}/.well-known/security.txt\nPolicy: https://mahoje.dk\n", encoding="utf-8")
    (dist / "humans.txt").write_text(
        f"/* TEAM */\n  Developer: Mads Holst Jensen\n  Site: https://mahoje.dk\n  Contact: mads@mahoje.dk\n  Location: Odense, Denmark\n\n"
        f"/* SITE */\n  Last update: {today}\n  Languages: English, Danish\n  Standards: HTML5, CSS3, JSON-LD\n"
        f"  Hosting: Cloudflare Pages\n  Source: {brand['github']}\n", encoding="utf-8")
    (dist / "_headers").write_text(HEADERS_TXT, encoding="utf-8")
    for lang, fname in (("en", "404.html"), ("da", "da/404.html")):
        nf = NOT_FOUND[lang]
        t = L10N[lang]
        links = "\n".join(f'        <li><a href="{h}">{l}</a></li>' for l, h in site.cfg["nav"][lang] if h.startswith("/"))
        home = ("/da/" if lang == "da" else "/", t["home"])
        links = f'        <li><a href="{home[0]}">{home[1]}</a></li>\n' + links
        search_url = "/da/search/" if lang == "da" else "/search/"
        html = _render(_partial("404.html"), dict(nf, lang=lang, links=links, search_url=search_url,
                                                   search_placeholder=t["search_placeholder"], search_label=t["search_label"]))
        html, _ = apply_shell(site, fname, fname, html, {}, title=nf["title"], kind="home")
        html = html.replace('<link rel="stylesheet" href="/style.css">',
                            '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
                            f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{pagepass.FONTS.get(site.cfg["brand"], pagepass.FONTS_DEFAULT)}&display=swap">\n'
                            + pagepass.THEME_SCRIPT + '\n'
                            f'<link rel="stylesheet" href="/style.css?v={pagepass.CSS_VERSION}">')
        (dist / fname).parent.mkdir(exist_ok=True)
        (dist / fname).write_text(html, encoding="utf-8")

    # search: one page per language, same index
    alts = {"en": own + "/search/", "da": own + "/da/search/"}
    for lang, fname in (("en", "search/index.html"), ("da", "da/search/index.html")):
        t = L10N[lang]
        search_url = "/da/search/" if lang == "da" else "/search/"
        html = _render(_partial("search.html"), dict(lang=lang, title=t["search_title"].format(brand=site.cfg["brand"]), heading=t["search_heading"],
                                                     description=t["search_description"], search_url=search_url,
                                                     search_placeholder=t["search_placeholder"], search_label=t["search_label"],
                                                     search_hint=t["search_hint"], noscript=t["noscript"]))
        html, _ = apply_shell(site, fname, fname, html, alts, title=t["search_title"].format(brand=site.cfg["brand"]), kind="page")
        html, _info = pagepass.normalize_head(html, site_url=own, brand=brand, lang=lang, dest=fname, canonical=own + search_url,
                                              alternates=alts, og_image=own + ("/og-da.png" if lang == "da" else "/og.png"),
                                              dates=None, github=site.cfg["github"], kind="page")
        (dist / fname).parent.mkdir(parents=True, exist_ok=True)
        (dist / fname).write_text(html, encoding="utf-8")

    index = [dict(url=p["url"].replace(own, "") or "/", title=p["title"], description=p["description"], lang=p["lang"],
                  section=p.get("section", ""), body=p.get("body", ""), tags=p.get("tags", [])) for p in pages]
    (dist / "search-index.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def write_site(site: Site, local: dict, global_idx: dict, kv_id: str, pairs: dict, dates: dict) -> list[dict]:
    dist = site.dist
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    own = "https://" + site.domain
    brand = BRANDS[site.cfg["product"]]
    pages: list[dict] = []
    # prev/next: blog and guide pages of the same language, newest first (first commit date)
    series: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for key, (src, dest) in site.files.items():
        if src.suffix.lower() != ".html":
            continue
        k = pagepass.page_kind(dest)
        if k not in ("article", "guide") or dest.endswith("index.html"):
            continue
        lg = "da" if dest.startswith("da/") else "en"
        try:
            rs = src.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            rs = ""
        dd = dates.get(rs, ("0000-00-00", "0000-00-00"))
        title = pagepass.clamp_title(title_of(src).split(" | ")[0] or dest)
        series.setdefault((k, lg), []).append((dd[0], canonical_url(dest), title))
    neighbours: dict[str, dict] = {}
    for lst in series.values():
        lst.sort(key=lambda x: (x[0], x[1]), reverse=True)
        for i, (_d, url, _t) in enumerate(lst):
            neighbours[url] = {"prev": (lst[i - 1][1], lst[i - 1][2]) if i > 0 else None,
                               "next": (lst[i + 1][1], lst[i + 1][2]) if i + 1 < len(lst) else None}
    for key, (src, dest) in site.files.items():
        out = dist / dest
        out.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() not in TEXT_EXT:
            shutil.copy2(src, out)
            continue
        text = src.read_text(encoding="utf-8", errors="surrogateescape")
        is_html = src.suffix.lower() in (".html", ".htm")
        if is_html and "brand" in site.cfg and BODY_RE.search(text):
            lang = "da" if re.search(r'<html[^>]*lang="da"', text[:400], re.I) else "en"
            page_url = own + canonical_url(dest)
            idx_cfg = site.cfg.get("index_from")
            idx_map = {"index.html": idx_cfg} if isinstance(idx_cfg, str) else (idx_cfg or {})
            idx_target = next((tgt for tgt, srcf in idx_map.items() if srcf == dest), None)
            if idx_target:  # source of an index copy: canonical is the index url
                page_url = own + canonical_url(idx_target)
            alts = pairs.get(page_url, {}) or pairs.get(own + canonical_url(dest), {})
            text = pagepass.normalize_body(text)
            try:
                rel_src = src.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                rel_src = ""
            d = dates.get(rel_src)
            kind = "home" if (idx_target or dest in ("index.html", "da/index.html")) else pagepass.page_kind(dest)
            raw_title = pagepass.clamp_title(title_of(src).split(" | ")[0] or dest)
            text, shell_info = apply_shell(site, key, dest, text, alts, title=raw_title, dates=d,
                                           neighbours=neighbours.get(canonical_url(dest), {}), kind=kind)
            ogs = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', text)
            og_image = og_image_for(site, ogs.group(1) if ogs else None, lang, local, global_idx)
            text, info = pagepass.normalize_head(
                text, site_url=own, brand=brand, lang=lang, dest=dest, canonical=page_url,
                alternates=alts, og_image=og_image, dates=d, github=site.cfg["github"],
                kind="home" if (idx_target or dest in ("index.html", "da/index.html")) else None)
            if shell_info["crumbs"]:
                ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "name": name, "item": own + url}
                    for i, (name, url) in enumerate(shell_info["crumbs"])]}
                text = re.sub(r"</head>", '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>\n</head>",
                              text, count=1, flags=re.I)
            mm = MAIN_OPEN_RE.search(text)
            main_txt = text_of(text[mm.end(): _main_end(text)]) if mm else ""
            main_txt = re.sub(r"^.*?" + re.escape(info["title"][:20]), "", main_txt, count=1) if info["title"][:20] in main_txt else main_txt
            tags = sorted({m.strip() for m in re.findall(r'<(?:span|div)\s+class="(?:badge|tag|tagchip)"[^>]*>([^<]{2,40})<', text)})
            pages.append(dict(dest=dest, url=page_url, lang=lang, alternates=alts, title=info["title"],
                              description=info["description"], lastmod=(d[1] if d else pagepass.now_iso()),
                              section=shell_info["section"], body=main_txt[:400].strip(), tags=tags))
        text = rewrite_text(site, text, is_html, local, global_idx)
        out.write_text(text, encoding="utf-8", errors="surrogateescape")

    idx_cfg = site.cfg.get("index_from")
    idx_map = {"index.html": idx_cfg} if isinstance(idx_cfg, str) else (idx_cfg or {})
    for target, source in idx_map.items():
        if not (dist / target).exists() and source and (dist / source).exists():
            shutil.copy2(dist / source, dist / target)
            src_pg = next((p for p in pages if p["dest"] == source), None)
            if src_pg:  # the copy is the canonical page; the source is a duplicate pointing at it
                src_pg["dest"] = target

    (dist / "wrangler.toml").write_text(
        f'name = "{site.project}"\n'
        f'compatibility_date = "2024-09-01"\n'
        f'pages_build_output_dir = "."\n\n'
        f'[[kv_namespaces]]\nbinding = "VISITS"\nid = "{kv_id}"\n',
        encoding="utf-8",
    )
    write_generated(site, pages)
    return pages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="build just this domain (index still spans all sites)")
    args = ap.parse_args()

    sites = {d: Site(d, c) for d, c in SITES.items()}
    select_files(sites)
    for s in sites.values():
        pulled = pull_assets(s)
        if pulled:
            print(f"  {s.domain}: pulled {pulled} referenced asset(s)")
    global_idx, local_idx = build_index(sites)
    kv_id = kv_namespace_id()
    pairs = hreflang_pairs(sites, global_idx, local_idx)
    dates = git_dates()

    DIST.mkdir(exist_ok=True)
    summary = {}
    for domain, s in sites.items():
        if args.only and domain != args.only:
            continue
        write_site(s, local_idx[domain], global_idx, kv_id, pairs, dates)
        n_files = sum(1 for p in s.dist.rglob("*") if p.is_file())
        n_html = sum(1 for _ in s.dist.rglob("*.html"))
        n_broken = sum(s.broken.values())
        summary[domain] = dict(project=s.project, files=n_files, html=n_html, shelled=s.shelled, rewritten=s.rewritten,
                               cross_domain=s.cross, broken=n_broken)
        print(f"\n== {domain} ({s.project}) -> dist/{domain}")
        print(f"   files: {n_files} ({n_html} html, {s.shelled} shelled)  rewritten: {s.rewritten}  cross-domain: {s.cross}  broken: {n_broken}")
        for path, n in sorted(s.broken.items(), key=lambda kv: -kv[1])[:15]:
            print(f"     broken {n:3d}x {path}")
        if len(s.broken) > 15:
            print(f"     ... and {len(s.broken) - 15} more distinct broken paths")
        if not (s.dist / "index.html").exists():
            print("   WARN: no index.html!")
    (DIST / "build-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
