#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
sys.path.insert(0, str(ROOT / "tools"))
from route_inventory import expected_urls as inventory_expected_urls, load_inventory
sys.path.insert(0, str(ROOT))
from build_sites import SITES, canonical_url, route_digest

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
GENERATED_NOINDEX = {"404.html", "da/404.html", "search/index.html", "da/search/index.html"}


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.canonicals: list[str] = []
        self.robots: list[str] = []
        self.in_head = False

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.casefold()
        if tag == "head":
            self.in_head = True
            return
        if not self.in_head:
            return
        attributes = {key.lower(): value or "" for key, value in attrs}
        if tag == "link" and "canonical" in attributes.get("rel", "").casefold().split():
            self.canonicals.append(attributes.get("href", ""))
        robots_key = attributes.get("name", attributes.get("http-equiv", "")).casefold()
        if tag == "meta" and robots_key == "robots":
            self.robots.extend(re.split(r"[\s,]+", attributes.get("content", "").casefold()))

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "head":
            self.in_head = False

    @property
    def noindex(self) -> bool:
        return "noindex" in self.robots or "none" in self.robots


def parse_head(text: str) -> HeadParser:
    parser = HeadParser()
    parser.feed(text)
    parser.close()
    return parser


def head_data(path: Path) -> HeadParser:
    return parse_head(path.read_text(encoding="utf-8", errors="ignore"))


def normalized_path(value: str) -> str:
    return urlparse(value).path.rstrip("/") or "/"


def alias_sources(domain: str) -> dict[str, str]:
    configured = SITES.get(domain, {}).get("index_from", {})
    if isinstance(configured, str):
        return {"index.html": configured}
    return dict(configured)


def worker_redirect_paths() -> set[str]:
    text = (ROOT / "site/_worker.js").read_text(encoding="utf-8")
    patterns = (
        (r"const DA_BLOG_REDIRECTS = \{(.*?)\};", "/blog/"),
        (r"const DA_BLOG_DUP_REDIRECTS = \{(.*?)\};", "/da/blog/"),
        (r"const EN_BLOG_BACK_REDIRECTS = \{(.*?)\};", "/da/blog/"),
        (r"const DA_SLUG_REDIRECTS = \{(.*?)\};", "/da/blog/"),
    )
    paths: set[str] = set()
    for pattern, prefix in patterns:
        match = re.search(pattern, text, re.S)
        if not match:
            raise ValueError(f"worker redirect table not found: {pattern}")
        paths.update(prefix + slug for slug in re.findall(r"['\"]([a-z0-9-]+)['\"]\s*:", match.group(1)))
    return paths


def parse_sitemap(path: Path) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    if not path.is_file():
        return [], [f"missing {path.name}"]
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        return [], [f"invalid sitemap.xml: {error}"]
    urls = []
    for entry in root.findall(f"{SITEMAP_NS}url"):
        location = entry.find(f"{SITEMAP_NS}loc")
        if location is None or not (location.text or "").strip():
            problems.append(f"sitemap entry without loc: {ET.tostring(entry, encoding='unicode')}")
            continue
        urls.append((location.text or "").strip())
    if not urls:
        problems.append("sitemap has no URLs")
    return urls, problems


def build_info_problems(path: Path, domain: str, sitemap_data: bytes, urls: list[str], expected_commit: str | None) -> list[str]:
    if not path.is_file():
        return ["missing build-info.json"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"invalid build-info.json: {error}"]
    problems = []
    expected = {
        "version": 1,
        "domain": domain,
        "sitemap_count": len(urls),
        "sitemap_sha256": hashlib.sha256(sitemap_data).hexdigest(),
        "routes_sha256": route_digest(urls),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            problems.append(f"build-info.json {key}={data.get(key)!r}, expected {value!r}")
    commit = str(data.get("commit", ""))
    if commit != "unknown" and not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        problems.append(f"build-info.json has invalid commit {commit!r}")
    if expected_commit and commit != expected_commit.lower():
        problems.append(f"build-info.json commit={commit!r}, expected {expected_commit.lower()!r}")
    return problems


def check_domain(domain: str, dist_root: Path = DIST, expected_commit: str | None = None,
                 inventory: dict[str, tuple[str, ...]] | None = None) -> list[str]:
    dist = dist_root / domain
    if not dist.is_dir():
        return [f"{domain}: missing build directory {dist}"]
    own = f"https://{domain}"
    aliases = alias_sources(domain)
    redirect_paths = worker_redirect_paths()
    try:
        expected_urls = inventory_expected_urls(domain, load_inventory() if inventory is None else inventory)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        return [f"{domain}: invalid route inventory: {error}"]
    discovered_urls: set[str] = set()
    normalized_discovered: dict[str, str] = {}
    excluded_urls: set[str] = set()
    alias_targets: list[tuple[str, str]] = []
    problems: list[str] = []

    html_paths = sorted(path for path in dist.rglob("*") if path.is_file() and path.suffix.lower() in (".html", ".htm"))
    for path in html_paths:
        relative = path.relative_to(dist).as_posix()
        route = canonical_url(relative)
        expected_url = own + route
        parser = head_data(path)
        generated = relative in GENERATED_NOINDEX
        if generated:
            if not parser.noindex:
                problems.append(f"{domain}/{relative}: generated route is not noindex")
            if len(parser.canonicals) > 1:
                problems.append(f"{domain}/{relative}: generated canonical count {len(parser.canonicals)}")
            canonical = parser.canonicals[0] if len(parser.canonicals) == 1 else None
            if canonical and canonical != expected_url:
                problems.append(f"{domain}/{relative}: generated canonical {canonical!r}, expected {expected_url!r}")
            continue
        if len(parser.canonicals) != 1:
            problems.append(f"{domain}/{relative}: canonical count {len(parser.canonicals)}")
            continue
        canonical = parser.canonicals[0]
        if parser.noindex:
            if canonical != expected_url:
                problems.append(f"{domain}/{relative}: noindex canonical {canonical!r}, expected {expected_url!r}")
            excluded_urls.add(canonical)
            continue
        if canonical != expected_url:
            if relative in aliases.values():
                alias_targets.append((relative, canonical))
            else:
                problems.append(f"{domain}/{relative}: undeclared canonical alias {canonical!r}")
            continue
        if normalized_path(route) in redirect_paths:
            problems.append(f"{domain}/{relative}: redirect-only route is indexable")
        route_key = normalized_path(canonical)
        if route_key in normalized_discovered and normalized_discovered[route_key] != canonical:
            problems.append(f"{domain}: slash-equivalent canonical routes {normalized_discovered[route_key]} and {canonical}")
        normalized_discovered.setdefault(route_key, canonical)
        if canonical in discovered_urls:
            problems.append(f"{domain}: multiple HTML files self-canonicalize {canonical}")
        discovered_urls.add(canonical)

    for source, target in alias_targets:
        if target not in discovered_urls:
            problems.append(f"{domain}/{source}: alias target {target!r} is not an indexable canonical route")
    for required in SITES.get(domain, {}).get("required_routes", []):
        if own + required not in expected_urls or own + required not in discovered_urls:
            problems.append(f"{domain}: required route missing {required}")

    for missing in sorted(expected_urls - discovered_urls):
        problems.append(f"{domain}: inventory route has no indexable canonical HTML {missing}")
    for extra in sorted(discovered_urls - expected_urls):
        problems.append(f"{domain}: indexable canonical route is not in inventory {extra}")

    sitemap_path = dist / "sitemap.xml"
    urls, sitemap_problems = parse_sitemap(sitemap_path)
    problems.extend(f"{domain}: {problem}" for problem in sitemap_problems)
    counts = Counter(urls)
    for url, count in sorted(counts.items()):
        if count > 1:
            problems.append(f"{domain}: duplicate sitemap URL {url} x{count}")
    for url in sorted(urls):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc.casefold() != domain.casefold() or parsed.query or parsed.fragment:
            problems.append(f"{domain}: invalid sitemap URL {url!r}")
        if normalized_path(parsed.path) in redirect_paths:
            problems.append(f"{domain}: redirect-only route present in sitemap {url}")
        if url in excluded_urls:
            problems.append(f"{domain}: noindex route present in sitemap {url}")
    actual_urls = set(urls)
    for missing in sorted(expected_urls - actual_urls):
        problems.append(f"{domain}: canonical route missing from sitemap {missing}")
    for extra in sorted(actual_urls - expected_urls):
        problems.append(f"{domain}: sitemap route has no indexable self-canonical HTML {extra}")

    robots_path = dist / "robots.txt"
    if not robots_path.is_file():
        problems.append(f"{domain}: missing robots.txt")
    else:
        robots = robots_path.read_text(encoding="utf-8")
        sitemap_lines = [line.split(":", 1)[1].strip() for line in robots.splitlines() if line.casefold().startswith("sitemap:")]
        if sitemap_lines != [f"{own}/sitemap.xml"]:
            problems.append(f"{domain}: robots sitemap lines {sitemap_lines!r}")
        for required in ("User-agent: *", "Allow: /", "Disallow: /api/"):
            if required not in robots.splitlines():
                problems.append(f"{domain}: robots.txt missing {required!r}")
        if "hermes-passiv.pages.dev" in robots:
            problems.append(f"{domain}: robots.txt references old origin")

    if sitemap_path.is_file():
        problems.extend(build_info_problems(dist / "build-info.json", domain, sitemap_path.read_bytes(), urls, expected_commit))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=sorted(SITES))
    parser.add_argument("--commit")
    args = parser.parse_args(argv)
    domains = [args.only] if args.only else list(SITES)
    failed = False
    for domain in domains:
        problems = check_domain(domain, expected_commit=args.commit)
        if problems:
            failed = True
            print(f"{domain}: {len(problems)} problem(s)")
            for problem in problems:
                print(f"- {problem}")
        else:
            print(f"{domain}: OK")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
