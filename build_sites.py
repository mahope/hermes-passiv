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
            "en": [("Install", "/#install"), ("CLI", "/clean-copy-cli-ref"), ("Web tool", "/clean-copy-tool"),
                   ("Blog", "/blog/"), ("GitHub", "https://github.com/mahope/clean-copy")],
            "da": [("Installér", "/da/#install"), ("CLI", "/clean-copy-cli-ref"), ("Webværktøj", "/clean-copy-tool"),
                   ("Blog", "/blog/"), ("GitHub", "https://github.com/mahope/clean-copy")],
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
            "en": [("Install", "/#install"), ("Pro", "/#pro"), ("Free checkers", "/tools/"),
                   ("FAQ", "/#faq"), ("GitHub", "https://github.com/mahope/deskuptime")],
            "da": [("Installér", "/da/#install"), ("Pro", "/da/#pro"), ("Gratis tjek", "/tools/"),
                   ("FAQ", "/da/#faq"), ("GitHub", "https://github.com/mahope/deskuptime")],
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
            "en": [("Install", "/#install"), ("Demo", "/bugbottle-demo"), ("Docs", "https://github.com/mahope/bugbottle#readme"),
                   ("npm", "https://www.npmjs.com/package/bugbottle"), ("GitHub", "https://github.com/mahope/bugbottle")],
            "da": [("Installér", "/da/#install"), ("Demo", "/bugbottle-demo"), ("Docs", "https://github.com/mahope/bugbottle#readme"),
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
            "en": [("Free tools", "/free-tools"), ("Downloads", "/free-downloads"), ("Blog", "/blog/"),
                   ("E-books", "/books/"), ("Compliance", "/compliance-guide")],
            "da": [("Gratis værktøjer", "/free-tools"), ("Downloads", "/free-downloads"), ("Blog", "/blog/"),
                   ("E-bøger", "/books/"), ("Compliance", "/da/compliance-site-check")],
        },
        "rest": True,
        "index_from": "free-tools.html",
    },
}

# Copied into every dist (never "claimed" by a single site).
SHARED = ["style.css", "track.js", "_worker.js"]
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
             "/icon-192.png", "/icon-512.png", "/site.webmanifest", "/og.png", "/og-da.png")


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
# Shared shell: header + footer partials injected into every HTML page.
# ---------------------------------------------------------------------------
PARTIALS = SITE / "_partials"
PRODUCTS = [
    ("Clean Copy", "https://cleancopy.tools"),
    ("DeskUptime", "https://deskuptime.com"),
    ("BugBottle", "https://bugbottle.dev"),
    ("Transmute", "https://transmute.run"),
    ("EU Comply Pro", "https://eucomplypro.com"),
    ("mahope.tools", "https://mahope.tools"),
]
L10N = {
    "en": dict(skip_label="Skip to content", nav_label="Main", menu_label="Menu", brand_by="by mahoje.dk",
               other_products_label="More from mahoje.dk", privacy_label="Privacy",
               privacy_note="No cookies, no trackers — only an anonymous page-view counter we run ourselves.",
               privacy_link="Privacy policy", terms_link="Terms",
               maker_note='Built by Mads Holst Jensen · <a href="https://mahoje.dk">mahoje.dk</a> — developer and technical partner, Odense, Denmark. Source on <a href="{github}">GitHub</a>.'),
    "da": dict(skip_label="Spring til indhold", nav_label="Hovedmenu", menu_label="Menu", brand_by="af mahoje.dk",
               other_products_label="Mere fra mahoje.dk", privacy_label="Privatliv",
               privacy_note="Ingen cookies, ingen trackere — kun en anonym sidevisningstæller, vi selv kører.",
               privacy_link="Privatlivspolitik", terms_link="Vilkår",
               maker_note='Lavet af Mads Holst Jensen · <a href="https://mahoje.dk">mahoje.dk</a> — udvikler og teknisk partner, Odense. Kildekode på <a href="{github}">GitHub</a>.'),
}
BODY_RE = re.compile(r"<body[^>]*>", re.I)
HEAD_END_RE = re.compile(r"</head>", re.I)
HTML_TAG_RE = re.compile(r"<html([^>]*)>", re.I)
FIRST_HEADER_RE = re.compile(r"\s*<header\b[^>]*>.*?</header>", re.S | re.I)
FOOTER_RE = re.compile(r"<footer\b[^>]*>.*?</footer>", re.S | re.I)
FOOTER_NAV_RE = re.compile(r'\s*<nav aria-label="Footer">.*?</nav>', re.S | re.I)
HREFLANG_RE = re.compile(r'<link[^>]+hreflang="(en|da)"[^>]+href="([^"]+)"|<link[^>]+href="([^"]+)"[^>]+hreflang="(en|da)"', re.I)


def _partial(name: str) -> str:
    return (PARTIALS / name).read_text(encoding="utf-8")


def _render(tpl: str, ctx: dict) -> str:
    return re.sub(r"\{\{(\w+)\}\}", lambda m: str(ctx.get(m.group(1), "")), tpl)


def _nav_links(links, current: str, indent: str = "      ") -> str:
    out = []
    for label, href in links:
        cur = ' aria-current="page"' if href == current else ""
        out.append(f'{indent}<a href="{href}"{cur}>{label}</a>')
    return "\n".join(out)


def _alternates(head: str) -> dict:
    alts = {}
    for m in HREFLANG_RE.finditer(head):
        lang, href = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
        alts.setdefault(lang.lower(), href)
    return alts


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


def apply_shell(site: Site, key: str, dest: str, text: str, alts: dict[str, str]) -> str:
    cfg = site.cfg
    if "brand" not in cfg or not BODY_RE.search(text):
        return text
    lang = "da" if re.search(r'<html[^>]*lang="da"', text[:400], re.I) else "en"
    t = L10N[lang]
    sw = ""
    if "en" in alts and "da" in alts and alts["en"] != alts["da"]:
        parts = []
        for code in ("en", "da"):
            if code == lang:
                parts.append(f'<span aria-current="true" lang="{code}">{code.upper()}</span>')
            else:
                parts.append(f'<a href="{alts[code]}" lang="{code}" hreflang="{code}">{code.upper()}</a>')
        sw = '      <span class="lang-switch">' + "".join(parts) + "</span>"
    current = canonical_url(dest)
    ctx = dict(t, brand=cfg["brand"], home="/da/" if lang == "da" else "/",
               nav=_nav_links(cfg["nav"][lang], current), lang_switch=sw,
               footer_links=_nav_links(cfg["nav"][lang], current, "        ").replace("<a ", "<li><a ").replace("</a>", "</a></li>"),
               product_links="\n".join(f'        <li><a href="{u}">{n}</a></li>' for n, u in PRODUCTS if not u.endswith(site.domain)),
               maker_note=t["maker_note"].format(github=cfg["github"]))
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
        if 'id="main"' not in text:
            text = re.sub(r"<main\b", '<main id="main"', text, count=1, flags=re.I)
        text = text[:body_start] + "\n" + header + text[body_start:]
    else:
        fpos = text.rfind('<footer class="site-footer">')
        inner = text[body_start:fpos]
        if 'class="container' not in inner and not re.search(r'class="[^"]*wrap', inner):
            inner = '\n<div class="container">' + inner + "</div>\n"
        text = text[:body_start] + "\n" + header + '\n<main id="main">' + inner + "</main>\n" + text[fpos:]
    site.shelled += 1
    return text


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
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data: blob: https:; connect-src 'self' https:; frame-src 'self' https://www.youtube-nocookie.com; worker-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self' https:; frame-ancestors 'none'; upgrade-insecure-requests

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
        links = "\n".join(f'        <li><a href="{h}">{l}</a></li>' for l, h in site.cfg["nav"][lang] if h.startswith("/"))
        home = ("/da/" if lang == "da" else "/", "Forside" if lang == "da" else "Home")
        links = f'        <li><a href="{home[0]}">{home[1]}</a></li>\n' + links
        html = _render(_partial("404.html"), dict(nf, lang=lang, links=links))
        html = apply_shell(site, fname, fname, html, {})
        html = html.replace('<link rel="stylesheet" href="/style.css">',
                            '<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n<link rel="stylesheet" href="/style.css">')
        (dist / fname).parent.mkdir(exist_ok=True)
        (dist / fname).write_text(html, encoding="utf-8")


def write_site(site: Site, local: dict, global_idx: dict, kv_id: str, pairs: dict, dates: dict) -> list[dict]:
    dist = site.dist
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    own = "https://" + site.domain
    brand = BRANDS[site.cfg["product"]]
    pages: list[dict] = []
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
            text = apply_shell(site, key, dest, text, alts)
            try:
                rel_src = src.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                rel_src = ""
            d = dates.get(rel_src)
            ogs = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', text)
            og_image = og_image_for(site, ogs.group(1) if ogs else None, lang, local, global_idx)
            text, info = pagepass.normalize_head(
                text, site_url=own, brand=brand, lang=lang, dest=dest, canonical=page_url,
                alternates=alts, og_image=og_image, dates=d, github=site.cfg["github"],
                kind="home" if (idx_target or dest in ("index.html", "da/index.html")) else None)
            pages.append(dict(dest=dest, url=page_url, lang=lang, alternates=alts, title=info["title"],
                              description=info["description"], lastmod=(d[1] if d else pagepass.now_iso())))
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
