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
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
DIST = ROOT / "dist"
AUDITEDWP_DESKUPTIME = ROOT.parent / "auditedwp" / "site" / "deskuptime"
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
        ],
        "title_match": [
            ("blog/*.html", r"Clean Copy|Markdown|clean-copy"),
            ("da/blog/*.html", r"Clean Copy|Markdown|clean-copy"),
        ],
        "index_from": "clean-copy.html",
    },
    "deskuptime.com": {
        "project": "deskuptime",
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
        ],
    },
    "mahope.tools": {
        "project": "mahope-tools",
        "rest": True,
        "index_from": "free-tools.html",
    },
}

# Copied into every dist (never "claimed" by a single site).
SHARED = ["style.css", "track.js", "_worker.js", "_headers"]
# Never copied (regenerated per site, or junk).
SKIP_NAMES = {"sitemap.xml", "robots.txt"}
SKIP_SUFFIXES = (".orig", ".bak")
# Root-relative refs to these extensions are auto-pulled into a dist if the
# file exists in site/ (og:image, icons, extra css/js…).
ASSET_EXT = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico", ".css", ".js", ".woff", ".woff2"}
TEXT_EXT = {".html", ".htm", ".xml", ".js", ".json", ".txt", ".md", ".yaml", ".yml", ".css", ".webmanifest"}
# Worker routes exist on every site; never count them as broken.
WORKER_PREFIXES = ("/api/", "/scan-proxy")


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
            if r in claimed or p.name in SKIP_NAMES or r.endswith(SKIP_SUFFIXES) or r in SHARED:
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
                if r in claimed or p.name in SKIP_NAMES or r.endswith(SKIP_SUFFIXES) or r in SHARED:
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
        for gen in ("/sitemap.xml", "/robots.txt", "/wrangler.toml"):
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


def kv_namespace_id() -> str:
    toml = (SITE / "wrangler.toml").read_text(encoding="utf-8")
    m = re.search(r'binding\s*=\s*"VISITS"\s*\n\s*id\s*=\s*"([0-9a-f]+)"', toml)
    if not m:
        sys.exit("Could not find VISITS kv id in site/wrangler.toml")
    return m.group(1)


def write_site(site: Site, local: dict, global_idx: dict, kv_id: str) -> None:
    dist = site.dist
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    for key, (src, dest) in site.files.items():
        out = dist / dest
        out.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() in TEXT_EXT:
            text = src.read_text(encoding="utf-8", errors="surrogateescape")
            text = rewrite_text(site, text, src.suffix.lower() in (".html", ".htm"), local, global_idx)
            out.write_text(text, encoding="utf-8", errors="surrogateescape")
        else:
            shutil.copy2(src, out)

    # index.html fallback
    idx = site.cfg.get("index_from")
    if not (dist / "index.html").exists() and idx and (dist / idx).exists():
        html = (dist / idx).read_text(encoding="utf-8")
        html = html.replace(f"https://{site.domain}{canonical_url(idx)}\"", f"https://{site.domain}/\"")
        (dist / "index.html").write_text(html, encoding="utf-8")

    # wrangler.toml (Pages flavour)
    (dist / "wrangler.toml").write_text(
        f'name = "{site.project}"\n'
        f'compatibility_date = "2024-09-01"\n'
        f'pages_build_output_dir = "."\n\n'
        f'[[kv_namespaces]]\nbinding = "VISITS"\nid = "{kv_id}"\n',
        encoding="utf-8",
    )

    # sitemap + robots
    pages = sorted(p for p in dist.rglob("*.html"))
    urls = []
    for p in pages:
        r = rel(p, dist)
        if r == "index.html" and idx and (dist / idx).exists() and site.files:
            pass  # keep "/" in the sitemap as well
        loc = f"https://{site.domain}{canonical_url(r)}"
        lastmod = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d")
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>")
    (dist / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n",
        encoding="utf-8",
    )
    robots = f"User-agent: *\nAllow: /\n\nSitemap: https://{site.domain}/sitemap.xml\n"
    if (dist / "llms.txt").exists():
        robots += f"\n# Machine-readable tool catalog for AI assistants\n# https://{site.domain}/llms.txt\n"
    (dist / "robots.txt").write_text(robots, encoding="utf-8")


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

    DIST.mkdir(exist_ok=True)
    summary = {}
    for domain, s in sites.items():
        if args.only and domain != args.only:
            continue
        write_site(s, local_idx[domain], global_idx, kv_id)
        n_files = sum(1 for p in s.dist.rglob("*") if p.is_file())
        n_html = sum(1 for _ in s.dist.rglob("*.html"))
        n_broken = sum(s.broken.values())
        summary[domain] = dict(project=s.project, files=n_files, html=n_html, rewritten=s.rewritten,
                               cross_domain=s.cross, broken=n_broken)
        print(f"\n== {domain} ({s.project}) -> dist/{domain}")
        print(f"   files: {n_files} ({n_html} html)  rewritten: {s.rewritten}  cross-domain: {s.cross}  broken: {n_broken}")
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
